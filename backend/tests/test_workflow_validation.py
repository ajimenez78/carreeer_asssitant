import asyncio
import tracemalloc

import pytest
from pydantic import ValidationError

from career_assistant.boundary import RequestBoundary
from career_assistant.workflow import Answer, SaveDefinition, SourceInput, SourceReview


@pytest.mark.parametrize(
    "value",
    [
        {
            "minimum": 100,
            "maximum": 50,
            "target": None,
            "currency": "EUR",
            "period": "year",
            "basis": "gross",
        },
        {
            "minimum": -1,
            "maximum": None,
            "target": None,
            "currency": None,
            "period": None,
            "basis": None,
        },
        {
            "minimum": None,
            "maximum": None,
            "target": None,
            "currency": "euros",
            "period": "year",
            "basis": "gross",
        },
        "good salary",
    ],
)
def test_compensation_requires_valid_explicit_structure(value):
    with pytest.raises(ValidationError):
        SaveDefinition(
            description="Staff",
            preferences=[{"key": "salary", "category": "compensation", "value": value}],
        )


def test_unknown_compensation_and_office_period_are_not_normalized():
    data = SaveDefinition(
        description="Staff",
        preferences=[
            {"key": "salary", "category": "compensation", "value": None},
            {
                "key": "onsite_limit",
                "category": "work_arrangement",
                "priority": "mandatory",
                "value": {"days": 2, "period": None},
            },
        ],
    )
    assert data.preferences[0].value is None
    assert data.preferences[1].value["period"] is None


@pytest.mark.parametrize(
    "category,value",
    [
        ("role", {"invented": "data"}),
        ("role", [1, {}]),
        ("role", "x" * 4001),
        ("work_arrangement", {"days": 2.5, "period": "week"}),
    ],
)
def test_invalid_or_excessive_preference_values_are_rejected(category, value):
    with pytest.raises(ValidationError):
        SaveDefinition(
            description="Staff",
            preferences=[{"key": "criterion", "category": category, "value": value}],
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"state": "answered"},
        {"state": "skipped", "answer": "Madrid"},
        {"state": "unknown", "answer": " "},
    ],
)
def test_answer_text_must_match_state(payload):
    with pytest.raises(ValidationError):
        Answer.model_validate(payload)


def test_sources_match_their_kind_and_review_is_explicit():
    with pytest.raises(ValidationError):
        SourceInput(kind="url", display_name="Profile", text="private text")
    assert (
        SourceInput(kind="url", display_name="Profile", url="HTTPS://example.com").url
        == "https://example.com"
    )
    with pytest.raises(ValidationError):
        SourceReview(facts=[" "])
    assert SourceReview(facts=[]).facts == []


@pytest.mark.parametrize("declared", [None, b"-1", b"invalid", b"999999999"])
def test_request_limits_work_with_chunked_or_invalid_length(declared):
    reached = []
    output = []

    async def app(scope, receive, send):
        reached.append(True)

    headers = [(b"origin", b"http://testserver")]
    if declared is not None:
        headers.append((b"content-length", declared))
    scope = {
        "type": "http",
        "path": "/api/job-definition",
        "method": "PUT",
        "headers": headers,
    }
    chunks = [
        {"type": "http.request", "body": b"x" * (256 * 1024), "more_body": True},
        {"type": "http.request", "body": b"x", "more_body": False},
    ]

    async def receive():
        return chunks.pop(0)

    async def send(message):
        output.append(message)

    asyncio.run(RequestBoundary(app, ["http://testserver"])(scope, receive, send))
    assert reached == []
    assert output[0]["status"] == 413


def test_many_tiny_chunks_cannot_amplify_upload_buffer_memory():
    sent = 0
    received = bytearray()

    async def receive():
        nonlocal sent
        sent += 1
        return {"type": "http.request", "body": b"x", "more_body": sent < 20_000}

    async def send(message):
        pass

    async def app(scope, receive, send):
        while True:
            message = await receive()
            received.extend(message["body"])
            if not message.get("more_body", False):
                break

    scope = {
        "type": "http",
        "path": "/api/job-definition",
        "method": "PUT",
        "headers": [(b"origin", b"http://testserver")],
    }
    tracemalloc.start()
    try:
        asyncio.run(RequestBoundary(app, ["http://testserver"])(scope, receive, send))
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert len(received) == 20_000
    assert peak < 1024 * 1024
