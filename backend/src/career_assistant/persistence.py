"""Small transactional operations for the current definition; callers own commits."""

from datetime import UTC, datetime
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from career_assistant.models import (
    BackgroundFact,
    Clarification,
    DocumentDeletion,
    JobDefinition,
    Owner,
    Preference,
    Source,
)

type Category = Literal[
    "role",
    "seniority",
    "responsibilities",
    "technical_interests",
    "company_context",
    "compensation",
    "location",
    "work_arrangement",
    "work_life_balance",
]


class PreferenceData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)

    key: str = Field(min_length=1, max_length=80)
    category: Category
    priority: Literal["mandatory", "preferred", "excluded"] = "preferred"
    value: JsonValue = None
    note: str | None = None


class DefinitionData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1)
    state: Literal["draft", "ready"] = "draft"
    preferences: list[PreferenceData] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_criteria(self) -> Self:
        if len({item.key for item in self.preferences}) != len(self.preferences):
            raise ValueError("Preference keys must be unique")
        return self


class SourceData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    kind: Literal["file", "url", "text"]
    display_name: str = Field(min_length=1)
    url: str | None = None
    object_key: UUID | None = None
    media_type: str | None = None
    size_bytes: int | None = None


def ensure_owner(session: Session) -> None:
    """Reserve the one owner without enabling login or resetting credentials."""
    session.execute(
        insert(Owner).values(id=1, username="owner").on_conflict_do_nothing()
    )


class DefinitionRepository:
    def __init__(self, session: Session):
        self.session = session

    def current(self, *, lock: bool = False) -> JobDefinition | None:
        statement = select(JobDefinition).where(JobDefinition.owner_id == 1)
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def require_current(self) -> JobDefinition:
        definition = self.current(lock=True)
        if definition is None:
            raise LookupError("Save a definition before adding context")
        return definition

    def save(self, data: DefinitionData) -> JobDefinition:
        owner = self.session.scalar(
            select(Owner).where(Owner.id == 1).with_for_update()
        )
        if owner is None:
            raise LookupError("Initialize the configured owner first")
        definition = self.current(lock=True)
        if definition is None:
            definition = JobDefinition(owner_id=1, description=data.description)
            self.session.add(definition)
            self.session.flush()
        definition.description = data.description
        definition.state = data.state
        definition.updated_at = datetime.now(UTC)
        existing = {
            item.key: item
            for item in self.session.scalars(
                select(Preference).where(Preference.definition_id == definition.id)
            )
        }
        for item in data.preferences:
            preference = existing.pop(item.key, None)
            if preference is None:
                preference = Preference(
                    definition_id=definition.id, **item.model_dump()
                )
                self.session.add(preference)
            else:
                for key, value in item.model_dump().items():
                    setattr(preference, key, value)
        for removed in existing.values():
            self.session.delete(removed)
        self.session.flush()
        return definition

    def add_source(self, data: SourceData) -> Source:
        definition = self.require_current()
        slot = None
        if data.kind == "file":
            occupied = set(
                self.session.scalars(
                    select(Source.file_slot).where(
                        Source.definition_id == definition.id
                    )
                )
            )
            slot = next((value for value in range(1, 6) if value not in occupied), None)
            if slot is None:
                raise ValueError("A definition can contain at most five uploaded files")
        source = Source(
            definition_id=definition.id, file_slot=slot, **data.model_dump()
        )
        self.session.add(source)
        self.session.flush()
        return source

    def source(self, source_id: UUID) -> Source:
        definition = self.require_current()
        source = self.session.scalar(
            select(Source).where(
                Source.id == source_id, Source.definition_id == definition.id
            )
        )
        if source is None:
            raise LookupError("Source not found in the current definition")
        return source

    def record_extraction(
        self, source_id: UUID, *, text: str | None, failed: bool = False
    ) -> Source:
        source = self.source(source_id)
        source.extraction_state = "failed" if failed else "ready"
        source.extracted_text = text
        source.reviewed_at = None
        self.session.execute(
            delete(BackgroundFact).where(BackgroundFact.source_id == source.id)
        )
        self._clear_clarifications(source.definition_id)
        self.session.flush()
        return source

    def review_source(self, source_id: UUID, facts: list[str]) -> Source:
        source = self.source(source_id)
        if source.extraction_state != "ready":
            raise ValueError("Extract source text before reviewing facts")
        if any(not fact.strip() for fact in facts):
            raise ValueError("Background facts must not be blank")
        self.session.execute(
            delete(BackgroundFact).where(BackgroundFact.source_id == source.id)
        )
        self.session.add_all(
            [
                BackgroundFact(source_id=source.id, content=fact.strip())
                for fact in facts
            ]
        )
        source.reviewed_at = datetime.now(UTC)
        self._clear_clarifications(source.definition_id)
        self.session.flush()
        return source

    def reviewed_background(self) -> list[BackgroundFact]:
        definition = self.require_current()
        return list(
            self.session.scalars(
                select(BackgroundFact)
                .join(Source)
                .where(
                    Source.definition_id == definition.id,
                    Source.reviewed_at.is_not(None),
                    Source.extraction_state == "ready",
                )
                .order_by(BackgroundFact.created_at, BackgroundFact.id)
            )
        )

    def add_clarifications(self, questions: list[str]) -> list[Clarification]:
        definition = self.require_current()
        if not 1 <= len(questions) <= 3 or any(not text.strip() for text in questions):
            raise ValueError("A round needs one to three nonempty questions")
        round_id = uuid4()
        rows = [
            Clarification(
                definition_id=definition.id,
                round_id=round_id,
                position=position,
                question=question.strip(),
            )
            for position, question in enumerate(questions, start=1)
        ]
        self.session.add_all(rows)
        self.session.flush()
        return rows

    def answer_clarification(
        self,
        question_id: UUID,
        state: Literal["answered", "skipped", "unknown"],
        answer: str | None = None,
    ) -> Clarification:
        definition = self.require_current()
        if (
            state not in {"answered", "skipped", "unknown"}
            or ((state == "answered") != bool(answer and answer.strip()))
            or (state != "answered" and answer is not None)
        ):
            raise ValueError("Answer text must match its answer state")
        question = self.session.scalar(
            select(Clarification).where(
                Clarification.id == question_id,
                Clarification.definition_id == definition.id,
            )
        )
        if question is None:
            raise LookupError("Clarification not found in the current definition")
        question.answer_state = state
        question.answer = answer.strip() if answer else None
        self.session.flush()
        return question

    def delete_source(self, source_id: UUID) -> None:
        source = self.source(source_id)
        self._queue_original(source)
        self._clear_clarifications(source.definition_id)
        self.session.delete(source)
        self.session.flush()

    def delete_definition(self) -> None:
        definition = self.require_current()
        for source in self.session.scalars(
            select(Source).where(Source.definition_id == definition.id)
        ):
            self._queue_original(source)
        self.session.delete(definition)
        self.session.flush()

    def _queue_original(self, source: Source) -> None:
        if source.object_key is not None:
            self.session.execute(
                insert(DocumentDeletion)
                .values(object_key=source.object_key)
                .on_conflict_do_nothing()
            )

    def _clear_clarifications(self, definition_id: UUID) -> None:
        self.session.execute(
            delete(Clarification).where(Clarification.definition_id == definition_id)
        )
