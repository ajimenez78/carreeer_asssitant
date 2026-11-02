"""Synthetic provider fixtures. Never imported by the production application."""

from career_assistant.ai import AIError, AIResult, Usage
from career_assistant.documents import SourceProcessor
from career_assistant.errors import AppError
from career_assistant.workflow import ChatProposal, ExtractedBackground

PASSWORD = "synthetic-browser-password"
BACKGROUND = "Historical Python experience. Education not provided."


def criterion(key, category, value, priority="preferred", note=None):
    return dict(key=key, category=category, value=value, priority=priority, note=note)


class WorkflowAI:
    failure = False
    sufficient = False

    def complete(self, *, instructions, data, response_type):
        if self.failure:
            raise AIError(
                "ai_unavailable", "The AI service is unavailable. Retry later."
            )
        if response_type == ChatProposal:
            unrelated = "interview" in data["current_message"].lower()
            value = {
                "reply": "I can help define your role."
                if unrelated
                else "Review the proposed hybrid limit before saving.",
                "in_scope": not unrelated,
                "preferences": []
                if unrelated
                else [
                    criterion(
                        "onsite_limit",
                        "work_arrangement",
                        {"days": 1, "period": "week"},
                        "mandatory",
                        "If hybrid",
                    )
                ],
                "questions": [],
                "conflicts": [],
            }
        elif response_type == ExtractedBackground:
            value = {
                "facts": [
                    {
                        "content": "Historical Python experience",
                        "evidence": "Historical Python",
                    }
                ],
                "unknowns": ["Education"],
            }
        else:
            spanish = data["language"] == "Spanish"
            value = {
                "preferences": [
                    criterion("seniority", "seniority", "Staff", "mandatory"),
                    criterion(
                        "architecture",
                        "responsibilities",
                        "Architecture and system design",
                    ),
                    criterion("remote", "work_arrangement", True),
                    criterion(
                        "hybrid_location",
                        "location",
                        "Madrid or nearby",
                        "mandatory",
                        "If hybrid",
                    ),
                    criterion(
                        "onsite_limit",
                        "work_arrangement",
                        {"days": 2, "period": None},
                        "mandatory",
                        "If hybrid",
                    ),
                    criterion("salary", "compensation", None),
                    criterion(
                        "frontend_only",
                        "responsibilities",
                        "Frontend-only work",
                        "excluded",
                    ),
                ],
                "questions": [
                    "What compensation range, currency, period, and gross/net basis?",
                    "What period covers the office-day limit?",
                    "What work–life balance boundaries matter?",
                ],
                "conflicts": [],
                "assessment": {
                    "summary": (
                        "Buscas un puesto de ingeniería Staff con arquitectura, "
                        "preferencia por trabajo remoto y una alternativa híbrida "
                        "cerca de Madrid."
                        if spanish
                        else "You are looking for a Staff engineering role involving "
                        "architecture, with remote work preferred and a conditional "
                        "hybrid option near Madrid."
                    ),
                    "sufficient": self.sufficient,
                    "explanation": (
                        (
                            "El puesto y las restricciones principales están claros."
                            if spanish
                            else "The role and its main constraints are clear."
                        )
                        if self.sufficient
                        else (
                            "Falta aclarar el período del límite de días presenciales."
                            if spanish
                            else "The office-day limit period remains unclear."
                        )
                    ),
                    "gaps": (
                        []
                        if self.sufficient
                        else [
                            "Período de los días presenciales"
                            if spanish
                            else "Office-day period"
                        ]
                    ),
                },
            }
        return AIResult(
            response_type.model_validate(value), "fixture", Usage(0, 0, 0, 0), 0
        )


class WorkflowProcessor(SourceProcessor):
    # File parsing is real. URL outcomes are deterministic; SSRF/fetch tests stay
    # in the backend suite and no external site is needed for routine browsers.
    def fetch(self, url):
        if "restricted" in url:
            raise AppError(
                "url_unavailable",
                "This page could not be retrieved. "
                "Upload a document or paste its text instead.",
                422,
            )
        return BACKGROUND
