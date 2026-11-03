"""Explicit two-generation synthetic check; skipped by routine test runs."""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest
from playwright.sync_api import expect
from workflow_fixtures import BACKGROUND, PASSWORD

from career_assistant.ai import OpenAIClient
from career_assistant.ai_evaluation import REFERENCE_DESCRIPTION
from career_assistant.config import Settings


def test_live_synthetic_workflow(page, workflow, request):
    if not request.config.getoption("--live-openai"):
        pytest.skip("Explicit --live-openai authorization is required")
    settings = Settings()
    client = OpenAIClient(settings)
    records = []
    checks = {}

    class RecordingAI:
        def complete(self, **kwargs):
            result = client.complete(**kwargs)
            cost = result.usage.estimated_cost_usd(settings.ai_model)
            records.append(
                {
                    "task": kwargs["response_type"].__name__,
                    "model": result.model,
                    "elapsed_seconds": round(result.elapsed_seconds, 3),
                    "usage": asdict(result.usage),
                    "estimated_cost_usd": str(cost) if cost is not None else None,
                }
            )
            return result

    origin, app, _, _ = workflow
    app.state.ai_client = RecordingAI()
    try:
        page.goto(origin)
        page.get_by_label("Username", exact=True).fill("owner")
        page.get_by_label("Password", exact=True).fill(PASSWORD)
        page.get_by_role("button", name="Sign in", exact=True).click()
        description = page.get_by_role(
            "textbox", name="The role you’re looking for", exact=True
        )
        description.fill(REFERENCE_DESCRIPTION)
        page.get_by_role("button", name="Save draft", exact=True).click()
        expect(page.get_by_role("status")).to_contain_text("Definition saved")
        navigation = page.get_by_role("navigation", name="Definition steps")
        navigation.get_by_role("button", name="02 Background").click()
        page.get_by_label("Document", exact=True).set_input_files(
            {
                "name": "synthetic-cv.md",
                "mimeType": "text/markdown",
                "buffer": BACKGROUND.encode(),
            }
        )
        page.get_by_role("button", name="Add source", exact=True).click()
        with page.expect_response("**/facts", timeout=65000) as response:
            page.get_by_role(
                "button", name="Suggest background facts", exact=True
            ).click()
        checks["background_request_succeeded"] = response.value.status == 200
        expect(page.get_by_label("Reviewed facts, one per line")).not_to_have_value("")
        page.get_by_role("button", name="Accept reviewed facts", exact=True).click()
        expect(page.get_by_role("status")).to_contain_text("Background facts accepted")
        navigation.get_by_role("button", name="03 Clarify").click()
        with page.expect_response("**/clarifications", timeout=65000) as response:
            page.get_by_role(
                "button", name="Request clarification & suggestions", exact=True
            ).click()
        checks["clarification_request_succeeded"] = response.value.status == 200
        proposal = response.value.json()
        preferences = proposal.get("proposal", {}).get("preferences", [])
        text = json.dumps(preferences).lower()
        checks["staff_scope_preserved"] = "staff" in text
        checks["architecture_preserved"] = "architect" in text
        checks["hybrid_location_preserved"] = "madrid" in text
        checks["onsite_period_stays_unknown"] = any(
            isinstance(p["value"], dict)
            and p["value"].get("days") == 2
            and p["value"].get("period") is None
            for p in preferences
        )
        checks["compensation_not_invented"] = all(
            p["value"] is None
            or isinstance(p["value"], dict)
            and all(p["value"].get(k) is None for k in ("minimum", "maximum", "target"))
            for p in preferences
            if p["category"] == "compensation"
        )
        checks["questions_present"] = bool(proposal.get("clarifications"))
        navigation.get_by_role("button", name="04 Review & save").click()
        page.get_by_role("button", name="Apply reviewed suggestions & save").click()
        expect(page.get_by_role("status")).to_contain_text("Definition saved")
        saved = page.request.get(origin + "/api/job-definition").json()
        page.reload()
        expect(description).to_have_value(REFERENCE_DESCRIPTION)
        description.fill(REFERENCE_DESCRIPTION + " I would also like flexible hours.")
        page.get_by_role("button", name="Save draft", exact=True).click()
        expect(page.get_by_role("status")).to_contain_text("Definition saved")
        refined = page.request.get(origin + "/api/job-definition").json()
        checks["save_reload_refine_preserves_identity_and_criteria"] = (
            refined["id"] == saved["id"]
            and refined["preferences"] == saved["preferences"]
        )
        checks["exactly_two_live_generations"] = len(records) == 2
        assert all(checks.values()), checks
    finally:
        client.close()
        Path("doc/features/job-definition/evidence/PART9_AI_WORKFLOW.json").write_text(
            json.dumps(
                {
                    "checked_at": datetime.now(UTC).isoformat(),
                    "synthetic_only": True,
                    "requested_model": settings.ai_model,
                    "checks": checks,
                    "results": records,
                },
                indent=2,
            )
            + "\n"
        )
