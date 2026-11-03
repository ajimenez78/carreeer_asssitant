"""Explicit synthetic clarity/summary quality check; never runs in routine tests."""

import json
from dataclasses import asdict
from pathlib import Path

from career_assistant.ai import AIError, OpenAIClient
from career_assistant.config import Settings
from career_assistant.workflow import propose


def preference(key, category, value, priority="preferred", note=None):
    return dict(key=key, category=category, priority=priority, value=value, note=note)


def cases():
    common = dict(
        definition_id="synthetic-role",
        reviewed_background=[
            dict(source_id="synthetic-cv", content="Historical Python experience")
        ],
        clarification_paused=False,
        control_version=0,
    )
    yield (
        "vague_en",
        "English",
        False,
        {
            **common,
            "description": (
                "Looking for an interesting job with good compensation and a good "
                "work-life balance."
            ),
            "accepted_preferences": [],
            "clarifications": [],
        },
    )
    yield (
        "clear_es_optional_unknown",
        "Spanish",
        True,
        {
            **common,
            "description": (
                "Busco un puesto Staff de ingeniería de software, con "
                "arquitectura y diseño de sistemas, colaboración entre equipos e "
                "interés en IA. Prefiero remoto en España. Solo acepto híbrido "
                "cerca de Madrid con un máximo de dos días por semana en oficina. "
                "Retribución entre 100.000 y 120.000 EUR brutos al año. Jornada "
                "de 32 horas semanales y sin guardias. No busco trabajo solo de "
                "frontend. El sector de la empresa me es indiferente."
            ),
            "accepted_preferences": [
                preference("role", "role", "Software Engineer"),
                preference("seniority", "seniority", "Staff", "mandatory"),
                preference(
                    "scope",
                    "responsibilities",
                    "Architecture, system design and cross-team collaboration",
                ),
                preference("ai", "technical_interests", "AI engineering"),
                preference("remote", "work_arrangement", True),
                preference("location", "location", "Spain", "mandatory"),
                preference(
                    "hybrid_location",
                    "location",
                    "Madrid or nearby",
                    "mandatory",
                    "If hybrid",
                ),
                preference(
                    "onsite",
                    "work_arrangement",
                    {"days": 2, "period": "week"},
                    "mandatory",
                    "If hybrid",
                ),
                preference(
                    "salary",
                    "compensation",
                    dict(
                        minimum=100000,
                        maximum=120000,
                        target=None,
                        currency="EUR",
                        period="year",
                        basis="gross",
                    ),
                ),
                preference(
                    "balance",
                    "work_life_balance",
                    "32 hours per week, no on-call",
                    "mandatory",
                ),
                preference(
                    "frontend_only",
                    "responsibilities",
                    "Frontend-only work",
                    "excluded",
                ),
                preference(
                    "industry",
                    "company_context",
                    None,
                    note="Explicitly unknown and flexible; not a blocker",
                ),
            ],
            "clarifications": [
                dict(
                    id="synthetic-question",
                    round_id="synthetic-round",
                    position=0,
                    question="Which industry do you want?",
                    answer_state="unknown",
                    answer=None,
                )
            ],
        },
    )


def main():
    settings = Settings()
    client = OpenAIClient(settings)
    records = []
    try:
        for name, language, expected, context in cases():
            result, _, _ = propose(client, context, language)
            assessment = result.value.assessment
            text = assessment.summary.lower()
            checks = {
                "appropriate_clarity_decision": assessment.sufficient == expected,
                "natural_language_summary_present": bool(assessment.summary.strip()),
                "background_not_promoted": "python" not in text,
                "focused_questions_or_clear_stop": not result.value.questions
                if expected
                else 0 < len(result.value.questions) <= 3,
            }
            if expected:
                checks.update(
                    staff_preserved="staff" in text,
                    conditional_madrid_limit_preserved="madrid" in text
                    and "semana" in text
                    and ("dos" in text or "2" in text),
                    explicit_optional_unknown_is_not_blocking=not assessment.gaps,
                )
            else:
                checks["vague_input_does_not_invent_staff"] = "staff" not in text
            cost = result.usage.estimated_cost_usd(settings.ai_model)
            records.append(
                dict(
                    case=name,
                    language=language,
                    assessment=assessment.model_dump(),
                    checks=checks,
                    model=result.model,
                    elapsed_seconds=round(result.elapsed_seconds, 3),
                    usage=asdict(result.usage),
                    estimated_cost_usd=str(cost) if cost is not None else None,
                )
            )
    except AIError as error:
        records.append(dict(error=dict(code=error.code, message=str(error))))
    finally:
        client.close()
    report = dict(synthetic_only=True, results=records)
    Path("doc/features/job-definition/evidence/CLARITY_AI_EVALUATION.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    passed = len(records) == 2 and all(
        all(r.get("checks", {}).values()) and "error" not in r for r in records
    )
    print(
        json.dumps(
            dict(
                passed=passed,
                cases=len(records),
                report="doc/features/job-definition/evidence/CLARITY_AI_EVALUATION.json",
            )
        )
    )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
