"""Private, explicit-save job-definition workflow."""

import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from career_assistant.ai import AIClient, OpenAIClient
from career_assistant.api.schemas import (
    BackgroundView,
    ChatTurnView,
    ChatView,
    ClarificationView,
    CleanupView,
    DefinitionView,
    QuestionView,
    SourceView,
)
from career_assistant.auth import require_owner, sessions
from career_assistant.documents import (
    MAX_FILE_BYTES,
    checked_text,
    validate_file,
)
from career_assistant.errors import AppError
from career_assistant.models import ChatTurn, DocumentDeletion
from career_assistant.persistence import (
    DefinitionData,
    DefinitionRepository,
    SourceData,
)
from career_assistant.storage import cleanup_documents, document_store
from career_assistant.workflow import (
    Answer,
    Assistance,
    ChatInput,
    ClarificationControl,
    SaveDefinition,
    SourceInput,
    SourceReview,
    ai_context,
    chat_turn_view,
    chat_turns,
    context_token,
    definition_view,
    discuss,
    extract_background,
    propose,
    question_view,
    source_view,
)

router = APIRouter(
    prefix="/api/job-definition",
    tags=["Job definition"],
    dependencies=[Depends(require_owner)],
)
STORAGE_ERRORS = (OSError, BotoCoreError, ClientError, AppError)


def store_for(request: Request):
    if request.app.state.store is not None:
        return request.app.state.store
    try:
        return document_store(request.app.state.settings)
    except ValueError:
        raise AppError(
            "storage_not_configured",
            "Check the backend document storage settings.",
            503,
        ) from None


def processor_for(request: Request):
    return request.app.state.processor


def ai_for(request: Request):
    if request.app.state.ai_client is not None:
        yield request.app.state.ai_client
        return
    client = OpenAIClient(request.app.state.settings)
    try:
        yield client
    finally:
        client.close()


def cleanup_status(request: Request) -> dict:
    try:
        cleanup_documents(sessions(request), store_for(request))
    except STORAGE_ERRORS:
        pass
    with sessions(request)() as session:
        remaining = session.scalar(select(func.count()).select_from(DocumentDeletion))
    return {"cleanup_pending": remaining > 0, "pending_originals": remaining}


@router.get("", response_model=DefinitionView)
def read_definition(request: Request):
    with sessions(request)() as session:
        return definition_view(session)


@router.put("", response_model=DefinitionView)
def save_definition(data: SaveDefinition, request: Request):
    with sessions(request).begin() as session:
        repo = DefinitionRepository(session)
        if data.proposal_context is not None:
            repo.require_current()
            if data.proposal_context != context_token(ai_context(session)):
                raise AppError(
                    "stale_proposal",
                    "Context changed. Generate a new proposal or edit manually.",
                    409,
                )
        repo.save(
            DefinitionData.model_validate(data.model_dump(exclude={"proposal_context"}))
        )
        return definition_view(session)


@router.patch("/clarification-control", response_model=DefinitionView)
def control_clarification(data: ClarificationControl, request: Request):
    with sessions(request).begin() as session:
        DefinitionRepository(session).set_clarification_paused(data.paused)
        return definition_view(session)


@router.delete(
    "",
    response_model=CleanupView,
    description="Delete the definition, sources, facts and answers. "
    "Original deletion may remain queued. Backups expire after seven days.",
)
def remove_definition(request: Request):
    with sessions(request).begin() as session:
        DefinitionRepository(session).delete_definition()
    return cleanup_status(request)


@router.post("/cleanup", response_model=CleanupView)
def retry_cleanup(request: Request):
    """Retry committed deletions, including after deleting the whole definition."""
    return cleanup_status(request)


def process_source(request: Request, source_id: UUID, content: bytes | None = None):
    factory = sessions(request)
    processor = processor_for(request)
    with factory.begin() as session:
        repo = DefinitionRepository(session)
        source = repo.source(source_id)
        kind, filename, url = source.kind, source.display_name, source.url
        if kind == "file":
            try:
                store = store_for(request)
                # Coordinate writes with deletion to prevent orphan files.
                if content is not None:
                    store.put(source.object_key, content)
                else:
                    content = store.get(source.object_key)
                source.original_stored = True
            except STORAGE_ERRORS:
                repo.record_extraction(source_id, text=None, failed=True)
                source.extraction_error = {
                    "code": "storage_unavailable",
                    "message": "Storage is unavailable. Retry or upload again.",
                }
                storage_failed = True
            else:
                storage_failed = False
        else:
            storage_failed = False
    if storage_failed:
        raise AppError(
            "storage_unavailable",
            "Original storage failed. Retry or remove the reserved source.",
            503,
            {"source_id": str(source_id)},
        )
    try:
        text = (
            processor.extract(filename, content)
            if kind == "file"
            else processor.fetch(url)
        )
        text = checked_text(text)
        error = None
    except AppError as failure:
        text = None
        error = {"code": failure.code, "message": str(failure)}
    with factory.begin() as session:
        repo = DefinitionRepository(session)
        source = repo.record_extraction(source_id, text=text, failed=error is not None)
        source.extraction_error = error
        return source_view(session, source, include_text=True)


@router.post(
    "/sources",
    status_code=201,
    response_model=SourceView,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": SourceInput.model_json_schema()},
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {"file": {"type": "string", "format": "binary"}},
                    }
                },
            },
        }
    },
)
async def add_source(request: Request):
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        async with request.form(
            max_files=1, max_fields=0, max_part_size=MAX_FILE_BYTES
        ) as form:
            file = form.get("file")
            if not isinstance(file, UploadFile) or len(form.multi_items()) != 1:
                raise AppError(
                    "invalid_upload", "Send one multipart file named 'file'.", 422
                )
            content = await file.read(MAX_FILE_BYTES + 1)
            filename, media_type = validate_file(file.filename or "", content)

        def reserve_file():
            with sessions(request).begin() as session:
                try:
                    return (
                        DefinitionRepository(session)
                        .add_source(
                            SourceData(
                                kind="file",
                                display_name=filename,
                                object_key=uuid4(),
                                media_type=media_type,
                                size_bytes=len(content),
                            )
                        )
                        .id
                    )
                except ValueError:
                    raise AppError(
                        "file_limit",
                        "Remove a file before uploading another; the limit is five.",
                        422,
                    ) from None

        source_id = await run_in_threadpool(reserve_file)
        return await run_in_threadpool(process_source, request, source_id, content)
    if request.headers.get("content-type", "").split(";", 1)[0] != "application/json":
        raise AppError(
            "unsupported_content_type", "Send a JSON source or multipart document.", 415
        )
    try:
        data = SourceInput.model_validate(await request.json())
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from None
    except json.JSONDecodeError, UnicodeDecodeError:
        raise AppError("invalid_json", "Send a valid JSON source.", 422) from None

    def reserve_source():
        with sessions(request).begin() as session:
            repo = DefinitionRepository(session)
            source = repo.add_source(
                SourceData(kind=data.kind, display_name=data.display_name, url=data.url)
            )
            if data.kind == "text":
                repo.record_extraction(source.id, text=checked_text(data.text))
            return source_view(session, source, include_text=True)

    result = await run_in_threadpool(reserve_source)
    if data.kind == "url":
        return await run_in_threadpool(process_source, request, result["id"])
    return result


@router.get("/sources/{source_id}", response_model=SourceView)
def read_source(source_id: UUID, request: Request):
    with sessions(request).begin() as session:
        return source_view(
            session, DefinitionRepository(session).source(source_id), include_text=True
        )


@router.patch("/sources/{source_id}", response_model=SourceView)
def review_source(source_id: UUID, data: SourceReview, request: Request):
    with sessions(request).begin() as session:
        repo = DefinitionRepository(session)
        source = repo.source(source_id)
        if source.extraction_state != "ready":
            raise AppError(
                "source_not_ready",
                "Extract usable text before reviewing this source.",
                409,
            )
        repo.review_source(source_id, data.facts)
        return source_view(session, source, include_text=True)


@router.post("/sources/{source_id}/retry", response_model=SourceView)
def retry_source(source_id: UUID, request: Request):
    with sessions(request).begin() as session:
        source = DefinitionRepository(session).source(source_id)
        if source.kind == "text":
            raise AppError(
                "retry_not_needed",
                "Pasted text needs no extraction retry. Review or replace the source.",
                409,
            )
    return process_source(request, source_id)


@router.get("/sources/{source_id}/original")
def download_original(source_id: UUID, request: Request):
    with sessions(request).begin() as session:
        source = DefinitionRepository(session).source(source_id)
        if source.kind != "file" or not source.original_stored:
            raise LookupError
        try:
            content = store_for(request).get(source.object_key)
        except STORAGE_ERRORS:
            raise AppError(
                "storage_unavailable", "The original cannot be read. Retry later.", 503
            ) from None
        return Response(
            content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment"},
        )


@router.delete(
    "/sources/{source_id}",
    response_model=CleanupView,
    description="Remove the original, source text and facts and clear "
    "all derived clarification context. Accepted preferences remain. "
    "Backups expire after seven days.",
)
def remove_source(source_id: UUID, request: Request):
    with sessions(request).begin() as session:
        DefinitionRepository(session).delete_source(source_id)
    return cleanup_status(request)


@router.post("/sources/{source_id}/facts", response_model=BackgroundView)
def suggest_facts(
    source_id: UUID,
    data: Assistance,
    request: Request,
    client: Annotated[AIClient, Depends(ai_for)],
):
    with sessions(request).begin() as session:
        source = DefinitionRepository(session).source(source_id)
        if source.extraction_state != "ready":
            raise AppError(
                "source_not_ready",
                "Extract usable text before asking for background facts.",
                409,
            )
        text = source.extracted_text
    result = extract_background(client, source_id, text, data.language)
    with sessions(request).begin() as session:
        source = DefinitionRepository(session).source(source_id)
        if source.extracted_text != text:
            raise AppError(
                "stale_proposal", "Source text changed. Generate facts again.", 409
            )
    return {
        "source_id": source_id,
        "proposal": result.value.model_dump(),
        "usage": usage_view(result),
    }


def usage_view(result):
    return {
        "model": result.model,
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "estimated_cost_usd": str(result.usage.estimated_cost_usd(result.model))
        if result.usage.estimated_cost_usd(result.model) is not None
        else None,
    }


@router.post("/clarifications", response_model=ClarificationView)
def clarify(
    data: Assistance, request: Request, client: Annotated[AIClient, Depends(ai_for)]
):
    with sessions(request).begin() as session:
        context = ai_context(session)
        if context["clarification_paused"]:
            raise AppError(
                "clarification_paused",
                "Clarification is stopped. Resume it before requesting another round.",
                409,
            )
    token = context_token(context)
    result, preferences, conflicts = propose(client, context, data.language)
    with sessions(request).begin() as session:
        repo = DefinitionRepository(session)
        repo.require_current()
        if context_token(ai_context(session)) != token:
            raise AppError(
                "stale_proposal",
                "The definition or context changed. Generate a new proposal.",
                409,
            )
        questions = (
            repo.add_clarifications(result.value.questions)
            if result.value.questions and not result.value.assessment.sufficient
            else []
        )
        # Include newly persisted questions in the token used to apply this proposal.
        token = context_token(ai_context(session))
        assessment = {
            **result.value.assessment.model_dump(),
            "language": data.language,
            "assessed_at": datetime.now(UTC).isoformat(),
            "context": token,
        }
        definition = repo.record_assessment(assessment)
        return {
            "proposal": {"preferences": preferences, "conflicts": conflicts},
            "clarifications": [question_view(row) for row in questions],
            "proposal_context": token,
            "assessment": assessment,
            "state": definition.state,
            "usage": usage_view(result),
        }


@router.patch("/clarifications/{question_id}", response_model=QuestionView)
def answer_question(question_id: UUID, data: Answer, request: Request):
    with sessions(request).begin() as session:
        row = DefinitionRepository(session).answer_clarification(
            question_id, data.state, data.answer
        )
        return question_view(row)


@router.get("/chat", response_model=ChatView)
def read_chat(request: Request):
    with sessions(request).begin() as session:
        return {
            "turns": [chat_turn_view(row) for row in chat_turns(session)],
            "context": context_token(ai_context(session)),
        }


def existing_turn(session, data):
    definition = DefinitionRepository(session).require_current()
    row = session.get(ChatTurn, data.request_id)
    if row is not None:
        if (
            row.definition_id != definition.id
            or row.message != data.message
            or row.language != data.language
        ):
            raise AppError(
                "chat_request_conflict",
                "Use a new request for a different message.",
                409,
            )
        return chat_turn_view(row)
    return None


@router.post("/chat", response_model=ChatTurnView)
def send_chat(
    data: ChatInput, request: Request, client: Annotated[AIClient, Depends(ai_for)]
):
    with sessions(request).begin() as session:
        previous = existing_turn(session, data)
        if previous is not None:
            return previous
        context = ai_context(session)
        if context["clarification_paused"]:
            raise AppError(
                "clarification_paused",
                "Clarification is stopped. Resume it before requesting another round.",
                409,
            )
    token = context_token(context)
    result, preferences, conflicts = discuss(
        client, context, data.message, data.language
    )
    with sessions(request).begin() as session:
        repo = DefinitionRepository(session)
        previous = existing_turn(session, data)
        if previous is not None:
            return previous
        if context_token(ai_context(session)) != token:
            raise AppError(
                "stale_proposal",
                "The definition or context changed. Generate a new proposal.",
                409,
            )
        has_changes = {p["key"]: p for p in preferences} != {
            p["key"]: p for p in context["accepted_preferences"]
        }
        row = repo.add_chat_turn(
            identity=data.request_id,
            message=data.message,
            language=data.language,
            response={
                "reply": result.value.reply,
                "in_scope": result.value.in_scope,
                "questions": result.value.questions,
                "proposal": {"preferences": preferences, "conflicts": conflicts},
                "has_changes": has_changes,
                "proposal_context": "",
                "usage": usage_view(result),
            },
        )
        row.response = {
            **row.response,
            "proposal_context": context_token(ai_context(session)),
        }
        session.flush()
        return chat_turn_view(row)
