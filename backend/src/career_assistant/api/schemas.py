"""Saved API representations shared with the upcoming frontend contract."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from career_assistant.persistence import PreferenceData
from career_assistant.workflow import Assessment, ExtractedBackground


class Representation(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceFailure(Representation):
    code: str
    message: str


class SourceMetadata(Representation):
    id: UUID
    kind: Literal["file", "url", "text"]
    display_name: str
    url: str | None
    media_type: str | None
    size_bytes: int | None
    extraction_state: Literal["pending", "ready", "failed"]
    extraction_error: SourceFailure | None
    original_stored: bool
    reviewed_at: datetime | None
    created_at: datetime


class FactView(Representation):
    id: UUID
    source_id: UUID
    content: str


class SourceView(SourceMetadata):
    extracted_text: str | None
    facts: list[FactView]


class QuestionView(Representation):
    id: UUID
    round_id: UUID
    position: int
    question: str
    answer_state: Literal["unanswered", "answered", "skipped", "unknown"]
    answer: str | None


class AssessmentView(Assessment):
    language: Literal["English", "Spanish"]
    assessed_at: datetime = Field(strict=False)
    context: str = Field(pattern="^[a-f0-9]{64}$")


class DefinitionView(Representation):
    id: UUID
    description: str
    state: Literal["draft", "ready"]
    assessment: AssessmentView | None
    clarification_paused: bool
    created_at: datetime
    updated_at: datetime
    preferences: list[PreferenceData]
    sources: list[SourceMetadata]
    clarifications: list[QuestionView]


class CleanupView(Representation):
    cleanup_pending: bool
    pending_originals: int


class UsageView(Representation):
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: str | None


class ProposedChanges(Representation):
    preferences: list[PreferenceData]
    conflicts: list[str]


class ClarificationView(Representation):
    proposal: ProposedChanges
    clarifications: list[QuestionView]
    proposal_context: str
    assessment: AssessmentView
    state: Literal["draft", "ready"]
    usage: UsageView


class BackgroundView(Representation):
    source_id: UUID
    proposal: ExtractedBackground
    usage: UsageView
