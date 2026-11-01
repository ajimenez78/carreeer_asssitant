import json
from decimal import Decimal

import httpx2 as httpx
import pytest
from openai import OpenAI
from pydantic import ValidationError

from career_assistant.ai import AIError, OpenAIClient
from career_assistant.ai_evaluation import Arithmetic
from career_assistant.config import Settings


def response_body(answer='{"answer":4}', **overrides):
    body = {
        "id": "resp_synthetic",
        "object": "response",
        "created_at": 0,
        "status": "completed",
        "model": "gpt-6-luna",
        "output": [
            {
                "id": "msg_synthetic",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": answer,
                        "annotations": [],
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": 100,
            "input_tokens_details": {"cached_tokens": 10},
            "output_tokens": 20,
            "output_tokens_details": {"reasoning_tokens": 5},
            "total_tokens": 120,
        },
    }
    body.update(overrides)
    return body


def completion(client):
    return client.complete(
        instructions="Compute arithmetic.",
        data={"question": "2+2"},
        response_type=Arithmetic,
    )


def mock_client(handler):
    sdk = OpenAI(
        api_key="synthetic-key",
        base_url="https://api.openai.com/v1",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return OpenAIClient(Settings(_env_file=None, openai_api_key=None), sdk=sdk)


def test_real_sdk_serializes_bounded_private_structured_requests():
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/input_tokens"):
            return httpx.Response(
                200, json={"object": "response.input_tokens", "input_tokens": 100}
            )
        return httpx.Response(200, json=response_body())

    client = mock_client(handler)
    try:
        result = completion(client)
    finally:
        client.close()
    assert result.value.answer == 4
    assert result.usage.reasoning_tokens == 5
    assert result.usage.estimated_cost_usd("gpt-6-luna") == Decimal("0.0000191")
    assert result.usage.estimated_cost_usd("unpriced-model") is None
    count, generate = [json.loads(request.content) for request in requests]
    assert requests[0].url.path == "/v1/responses/input_tokens"
    assert requests[1].url.path == "/v1/responses"
    for name in ("model", "instructions", "input", "text", "reasoning", "truncation"):
        assert count[name] == generate[name]
    assert generate["reasoning"] == {"effort": "low"}
    assert generate["max_output_tokens"] == 2000
    assert generate["store"] is False
    assert generate["truncation"] == "disabled"
    assert generate["service_tier"] == "default"
    assert generate["text"]["format"]["strict"] is True
    assert generate["text"]["format"]["schema"]["additionalProperties"] is False
    assert generate["text"]["format"]["schema"]["required"] == ["answer"]
    assert "tools" not in generate


def test_input_token_limit_prevents_inference():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200, json={"object": "response.input_tokens", "input_tokens": 20001}
        )

    client = mock_client(handler)
    try:
        with pytest.raises(AIError) as error:
            completion(client)
    finally:
        client.close()
    assert error.value.code == "ai_input_too_large"
    assert error.value.status == 413
    assert len(requests) == 1


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        (401, "invalid_api_key", "ai_access_denied"),
        (403, "permission_denied", "ai_access_denied"),
        (404, "model_not_found", "ai_model_unavailable"),
        (429, "insufficient_quota", "ai_quota_exceeded"),
        (429, "rate_limit_exceeded", "ai_throttled"),
        (400, "invalid_parameter", "ai_request_rejected"),
        (422, "invalid_schema", "ai_request_rejected"),
        (500, "server_error", "ai_unavailable"),
    ],
)
def test_provider_errors_are_safe_and_not_retried(status, code, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            status,
            json={
                "error": {
                    "message": "Synthetic sensitive provider diagnostic",
                    "type": code,
                    "code": code,
                }
            },
        )

    client = mock_client(handler)
    try:
        with pytest.raises(AIError) as error:
            completion(client)
    finally:
        client.close()
    assert error.value.code == expected
    assert "sensitive" not in str(error.value)
    assert len(requests) == 1


@pytest.mark.parametrize(
    ("exception", "code", "status"),
    [
        (httpx.ReadTimeout, "ai_timeout", 504),
        (httpx.ConnectError, "ai_unavailable", 503),
    ],
)
def test_transport_failure_is_safe(exception, code, status):
    def handler(request):
        raise exception("Synthetic sensitive network diagnostic", request=request)

    client = mock_client(handler)
    try:
        with pytest.raises(AIError) as error:
            completion(client)
    finally:
        client.close()
    assert error.value.code == code
    assert error.value.status == status
    assert "sensitive" not in str(error.value)


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (response_body(answer='{"answer":"four"}'), "ai_invalid_response"),
        (
            response_body(answer='{"answer":4,"invented":"extra"}'),
            "ai_invalid_response",
        ),
        (response_body(answer='{"answer":'), "ai_invalid_response"),
        (
            response_body(
                status="incomplete", incomplete_details={"reason": "max_output_tokens"}
            ),
            "ai_incomplete",
        ),
        (response_body(status="failed"), "ai_incomplete"),
        (response_body(output=[]), "ai_invalid_response"),
        (response_body(usage=None), "ai_invalid_response"),
        (
            response_body(
                output=[
                    {
                        "id": "msg_refusal",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "refusal", "refusal": "Synthetic refusal"}
                        ],
                    }
                ]
            ),
            "ai_refused",
        ),
    ],
)
def test_invalid_incomplete_and_refused_output_never_becomes_a_result(body, code):
    def handler(request):
        if request.url.path.endswith("/input_tokens"):
            return httpx.Response(
                200, json={"object": "response.input_tokens", "input_tokens": 100}
            )
        return httpx.Response(200, json=body)

    client = mock_client(handler)
    try:
        with pytest.raises(AIError) as error:
            completion(client)
    finally:
        client.close()
    assert error.value.code == code
    if body["usage"] is not None:
        assert error.value.usage.output_tokens == 20


def test_settings_limits_and_backend_key_do_not_leak(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://untrusted.example.invalid")
    settings = Settings(_env_file=None, openai_api_key="synthetic-secret")
    assert "synthetic-secret" not in repr(settings)
    assert "synthetic-secret" not in settings.model_dump_json()
    client = OpenAIClient(settings)
    try:
        assert str(client.sdk.base_url) == "https://api.openai.com/v1/"
        assert client.sdk.max_retries == 0
        assert client.sdk.timeout == 60
    finally:
        client.close()
    for key, value in [
        ("ai_max_input_tokens", 20001),
        ("ai_max_output_tokens", 2001),
        ("ai_timeout_seconds", 61),
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{key: value})


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_key_is_actionable_without_opening_a_connection(key):
    with pytest.raises(AIError) as error:
        OpenAIClient(Settings(_env_file=None, openai_api_key=key))
    assert error.value.code == "ai_not_configured"


def test_preflight_uses_the_remaining_timeout_budget(monkeypatch):
    clock = iter([0.0, 61.0])
    monkeypatch.setattr("career_assistant.ai.monotonic", lambda: next(clock))
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200, json={"object": "response.input_tokens", "input_tokens": 100}
        )

    client = mock_client(handler)
    try:
        with pytest.raises(AIError) as error:
            completion(client)
    finally:
        client.close()
    assert error.value.code == "ai_timeout"
    assert len(calls) == 1
