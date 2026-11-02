"""Synthetic chat workflow over real PostgreSQL and the authenticated API."""

from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from test_workflow_api import ROOT, api, criterion, save, source  # noqa: F401

from career_assistant.ai import AIError, AIResult, Usage
from career_assistant.main import create_app
from career_assistant.workflow import ChatProposal


@pytest.fixture
def chat(request):
    workflow_api = request.getfixturevalue("api")
    client, ai, store, app = workflow_api
    original = ai.complete
    ai.chat_output = {
        "reply": "Review changing the hybrid limit to one day per week.",
        "in_scope": True,
        "preferences": [
            criterion("onsite_limit", "work_arrangement", {"days": 1, "period": "week"})
        ],
        "questions": [],
        "conflicts": [],
    }

    def complete(**kwargs):
        if kwargs["response_type"] != ChatProposal:
            return original(**kwargs)
        ai.calls.append(kwargs)
        if ai.callback:
            ai.callback()
        if ai.failure:
            raise ai.failure
        return AIResult(
            SimpleNamespace(
                **ai.chat_output, model_dump=lambda: deepcopy(ai.chat_output)
            ),
            "gpt-6-luna",
            Usage(100, 0, 50, 0),
            0.1,
        )

    ai.complete = complete
    save(
        client,
        preferences=[
            criterion(),
            criterion(
                "onsite_limit", "work_arrangement", {"days": 2, "period": "week"}
            ),
        ],
    )
    return workflow_api


def send(
    client,
    message="Change hybrid availability to at most 1 day per week.",
    request_id=None,
):
    return client.post(
        ROOT + "/chat",
        json={
            "request_id": request_id or str(uuid4()),
            "message": message,
            "language": "Spanish",
        },
    )


def test_chat_review_save_reload_restart_and_idempotency(chat):
    client, ai, store, app = chat
    before = client.get(ROOT).json()
    request_id = str(uuid4())
    result = send(client, request_id=request_id)
    assert result.status_code == 200, result.text
    turn = result.json()
    assert turn["has_changes"] and turn["proposal"]["conflicts"]
    assert client.get(ROOT).json()["preferences"] == before["preferences"]
    assert client.get(ROOT + "/chat").json()["turns"] == [turn]
    assert ai.calls[-1]["data"]["language"] == "Spanish"
    assert send(client, request_id=request_id).json() == turn
    assert len(ai.calls) == 1
    assert send(client, "A different message", request_id).status_code == 409
    saved = save(
        client,
        preferences=turn["proposal"]["preferences"],
        proposal_context=turn["proposal_context"],
    )
    assert next(p for p in saved["preferences"] if p["key"] == "onsite_limit")[
        "value"
    ] == {"days": 1, "period": "week"}
    assert (
        next(p for p in saved["preferences"] if p["key"] == "seniority")["value"]
        == "Staff"
    )
    restarted = create_app(
        app.state.settings, sessions=app.state.sessions, ai_client=ai, store=store
    )
    with TestClient(
        restarted, headers={"Origin": "http://testserver"}, cookies=dict(client.cookies)
    ) as reopened:
        assert reopened.get(ROOT).json()["preferences"] == saved["preferences"]
        history = reopened.get(ROOT + "/chat").json()
        assert (
            history["turns"] == [turn]
            and history["context"] != turn["proposal_context"]
        )
    send(client, "Keep all other preferences.")
    context = ai.calls[-1]["data"]
    assert context["conversation"][0]["message"].startswith("Change hybrid")
    assert "proposed_changes_not_accepted" in context["conversation"][0]


def test_ambiguous_and_unrelated_chat_keep_accepted_data(chat):
    client, ai, *_ = chat
    ai.chat_output.update(
        preferences=[],
        reply="Which period covers the limit?",
        questions=["Per week or month?"],
    )
    before = client.get(ROOT).json()["preferences"]
    result = send(client, "Maybe fewer office days?").json()
    assert not result["has_changes"] and result["questions"]
    assert result["proposal"]["preferences"] == before
    ai.chat_output.update(
        in_scope=False, questions=[], reply="I can help define your ideal role."
    )
    saved = client.get(ROOT).json()
    result = send(client, "Find jobs and prepare an interview")
    assert result.status_code == 200 and not result.json()["has_changes"]
    assert client.get(ROOT).json() == saved


@pytest.mark.parametrize(
    "invalid",
    [
        {"preferences": [criterion(value={"bad": "shape"})]},
        {"preferences": [criterion(), criterion()]},
        {
            "preferences": [
                criterion(
                    "salary",
                    "compensation",
                    {
                        "minimum": 10,
                        "maximum": 1,
                        "target": None,
                        "currency": "EUR",
                        "period": "year",
                        "basis": "gross",
                    },
                )
            ]
        },
        {"reply": "   "},
        {"questions": [" "]},
        {"in_scope": False},
    ],
)
def test_invalid_model_output_is_atomic(chat, invalid):
    client, ai, *_ = chat
    before = client.get(ROOT).json()
    ai.chat_output.update(invalid)
    response = send(client)
    assert response.status_code == 502, response.text
    assert client.get(ROOT).json() == before
    assert client.get(ROOT + "/chat").json()["turns"] == []


def test_provider_failure_and_stale_calls_preserve_accepted_data(chat):
    client, ai, *_ = chat
    before = client.get(ROOT).json()["preferences"]
    ai.failure = AIError("ai_timeout", "AI timed out", 504)
    assert send(client).status_code == 504
    ai.failure = None
    ai.callback = lambda: save(
        client, preferences=before, description="A newer structured edit"
    )
    assert send(client).status_code == 409
    assert client.get(ROOT + "/chat").json()["turns"] == []
    ai.callback = lambda: client.patch(
        ROOT + "/clarification-control", json={"paused": True}
    )
    assert send(client).status_code == 409
    ai.callback = None
    calls = len(ai.calls)
    assert send(client).status_code == 409
    assert len(ai.calls) == calls
    assert client.get(ROOT).json()["preferences"] == before


def test_source_deletion_removes_chat_and_late_proposals(chat):
    client, ai, *_ = chat
    sid = source(client, "Synthetic private background snippet")["id"]
    client.patch(
        f"{ROOT}/sources/{sid}",
        json={"facts": ["Synthetic private background snippet"]},
    )
    turn = send(client).json()
    assert ai.calls[-1]["data"]["reviewed_background"]
    before = client.get(ROOT).json()["preferences"]
    assert client.delete(f"{ROOT}/sources/{sid}").status_code == 200
    assert client.get(ROOT + "/chat").json()["turns"] == []
    assert (
        client.put(
            ROOT,
            json={
                "description": "New description",
                "preferences": turn["proposal"]["preferences"],
                "proposal_context": turn["proposal_context"],
            },
        ).status_code
        == 409
    )
    send(client)
    assert ai.calls[-1]["data"]["conversation"] == []
    assert ai.calls[-1]["data"]["reviewed_background"] == []
    assert client.get(ROOT).json()["preferences"] == before
    assert client.delete(ROOT).status_code == 200
    assert client.get(ROOT + "/chat").status_code == 404
    save(client)
    assert client.get(ROOT + "/chat").json()["turns"] == []


def test_chat_invalidates_assessment_and_structured_proposals(chat):
    client, *_ = chat
    assessed = client.post(ROOT + "/clarifications", json={}).json()
    assert client.get(ROOT).json()["assessment"]
    send(client)
    assert client.get(ROOT).json()["assessment"] is None
    response = client.put(
        ROOT,
        json={
            "description": "New description",
            "preferences": assessed["proposal"]["preferences"],
            "proposal_context": assessed["proposal_context"],
        },
    )
    assert response.status_code == 409


def test_chat_private_and_message_limits(chat):
    client, *_ = chat
    assert send(client, " ").status_code == 422
    assert send(client, "x" * 4001).status_code == 422
    assert client.post(ROOT + "/chat", json={"message": "A message"}).status_code == 422
    client.delete("/api/session")
    assert client.get(ROOT + "/chat").status_code == 401
    assert send(client).status_code == 401


def test_concurrent_retry_returns_the_committed_turn_once(chat):
    client, ai, *_ = chat
    identity = str(uuid4())

    def overlapping_retry():
        ai.callback = None
        assert send(client, request_id=identity).status_code == 200

    ai.callback = overlapping_retry
    response = send(client, request_id=identity)
    assert response.status_code == 200
    assert client.get(ROOT + "/chat").json()["turns"] == [response.json()]


def test_rapid_stop_resume_rejects_late_chat_and_source_deletion_clears_it(chat):
    client, ai, *_ = chat

    def stop_resume():
        client.patch(ROOT + "/clarification-control", json={"paused": True})
        client.patch(ROOT + "/clarification-control", json={"paused": False})

    ai.callback = stop_resume
    assert send(client).status_code == 409
    assert client.get(ROOT + "/chat").json()["turns"] == []
    sid = source(client)["id"]
    ai.callback = lambda: client.delete(f"{ROOT}/sources/{sid}")
    assert send(client).status_code == 409
    assert client.get(ROOT + "/chat").json()["turns"] == []
