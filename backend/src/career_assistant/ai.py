"""Backend-only structured Responses API boundary; no database writes or API routes."""

import json
from dataclasses import dataclass
from decimal import Decimal
from time import monotonic
from typing import Protocol

from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, OpenAI
from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from career_assistant.config import Settings

OPENAI_BASE_URL = "https://api.openai.com/v1"


class AIOutput(BaseModel):
    """Structured schemas require explicit fields, including nullable unknowns."""

    model_config = ConfigDict(extra="forbid", strict=True)


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int

    def estimated_cost_usd(self, model: str) -> Decimal | None:
        # Standard short-context rates verified 2026-11-01; no cache-write requests.
        if model != "gpt-6-luna":
            return None
        return (
            Decimal(self.input_tokens - self.cached_input_tokens) * Decimal("0.10")
            + Decimal(self.cached_input_tokens) * Decimal("0.01")
            + Decimal(self.output_tokens) * Decimal("0.50")
        ) / 1_000_000


@dataclass(frozen=True)
class AIResult[T: AIOutput]:
    value: T
    model: str
    usage: Usage
    elapsed_seconds: float


class AIError(Exception):
    """Safe errors for the future HTTP layer; never contain raw provider payloads."""

    def __init__(
        self, code: str, message: str, status: int = 503, usage: Usage | None = None
    ):
        super().__init__(message)
        self.code = code
        self.status = status
        self.usage = usage


class AIClient(Protocol):
    def complete[T: AIOutput](
        self, *, instructions: str, data: dict[str, JsonValue], response_type: type[T]
    ) -> AIResult[T]: ...


def provider_error(error: APIError) -> AIError:
    if isinstance(error, APITimeoutError):
        return AIError(
            "ai_timeout", "AI request timed out. Retry or edit manually.", 504
        )
    if isinstance(error, APIConnectionError):
        return AIError("ai_unavailable", "AI connection failed. Retry later.")
    if isinstance(error, APIStatusError):
        if error.status_code in {401, 403}:
            return AIError(
                "ai_access_denied", "Check the backend OpenAI account and key."
            )
        if error.status_code == 404:
            return AIError(
                "ai_model_unavailable", "The configured AI model is unavailable."
            )
        if error.status_code == 429:
            if error.code == "insufficient_quota":
                return AIError(
                    "ai_quota_exceeded", "Check OpenAI billing and usage limits."
                )
            return AIError("ai_throttled", "AI rate limit reached. Retry later.")
        if error.status_code in {400, 422}:
            return AIError(
                "ai_request_rejected", "AI rejected the request configuration.", 502
            )
    return AIError("ai_unavailable", "The AI service is unavailable. Retry later.")


class OpenAIClient:
    def __init__(self, settings: Settings, *, sdk: OpenAI | None = None):
        self.settings = settings
        if sdk is None:
            if (
                settings.openai_api_key is None
                or not settings.openai_api_key.get_secret_value().strip()
            ):
                raise AIError(
                    "ai_not_configured", "Set backend OPENAI_API_KEY to enable AI."
                )
            sdk = OpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                base_url=OPENAI_BASE_URL,
                timeout=settings.ai_timeout_seconds,
                max_retries=0,
            )
        self.sdk = sdk

    def close(self) -> None:
        self.sdk.close()

    def complete[T: AIOutput](
        self, *, instructions: str, data: dict[str, JsonValue], response_type: type[T]
    ) -> AIResult[T]:
        started = monotonic()
        text = {
            "format": {
                "type": "json_schema",
                "name": response_type.__name__,
                "schema": response_type.model_json_schema(),
                "strict": True,
            }
        }
        request = {
            "model": self.settings.ai_model,
            "instructions": instructions,
            "input": json.dumps(data, ensure_ascii=False, allow_nan=False),
            "text": text,
            "reasoning": {"effort": self.settings.ai_reasoning_effort},
            "truncation": "disabled",
        }
        try:
            count = self.sdk.responses.input_tokens.count(
                **request,
                timeout=self.settings.ai_timeout_seconds,
            )
            if not isinstance(count.input_tokens, int) or count.input_tokens < 0:
                raise AIError("ai_invalid_response", "AI token count is invalid.", 502)
            if count.input_tokens > self.settings.ai_max_input_tokens:
                raise AIError(
                    "ai_input_too_large",
                    "Reduce the reviewed context before retrying.",
                    413,
                )
            remaining = self.settings.ai_timeout_seconds - (monotonic() - started)
            if remaining <= 0:
                raise AIError("ai_timeout", "AI request timed out. Retry later.", 504)
            response = self.sdk.responses.create(
                **request,
                max_output_tokens=self.settings.ai_max_output_tokens,
                service_tier="default",
                store=False,
                timeout=remaining,
            )
        except APIError as error:
            raise provider_error(error) from None

        usage = None
        if response.usage is not None:
            usage = Usage(
                input_tokens=response.usage.input_tokens,
                cached_input_tokens=response.usage.input_tokens_details.cached_tokens,
                output_tokens=response.usage.output_tokens,
                reasoning_tokens=response.usage.output_tokens_details.reasoning_tokens,
            )
        if response.status != "completed":
            raise AIError(
                "ai_incomplete",
                "AI did not complete its response. Retry or edit manually.",
                502,
                usage,
            )
        if any(
            part.type == "refusal"
            for item in response.output
            if item.type == "message"
            for part in item.content
        ):
            raise AIError(
                "ai_refused",
                "AI could not provide a suggestion. Edit manually.",
                502,
                usage,
            )
        if usage is None:
            raise AIError("ai_invalid_response", "AI usage data is missing.", 502)
        try:
            value = response_type.model_validate_json(response.output_text)
        except ValidationError:
            raise AIError(
                "ai_invalid_response",
                "AI returned invalid structured data. Retry or edit manually.",
                502,
                usage,
            ) from None
        return AIResult(value, response.model, usage, monotonic() - started)
