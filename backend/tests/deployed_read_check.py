"""Opt-in deployed smoke check; temporary session, no saved-content edits or AI."""

import base64
import json
import os
import traceback
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx2
from itsdangerous import TimestampSigner
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from career_assistant.config import Settings
from career_assistant.database import database_engine, database_url
from career_assistant.models import JobDefinition, OwnerSession, Source
from career_assistant.storage import document_store


def main():
    url = os.environ["CAREER_DEPLOYED_URL"].rstrip("/")
    local = Settings()
    remote = Settings(_env_file=".env.operations.local", document_backend="s3")
    engine = database_engine(database_url(remote))
    sessions = sessionmaker(engine)
    identity = uuid4()
    report = {"url": url}
    stage = "prepare verification session"
    try:
        with sessions.begin() as session:
            description = session.scalar(select(JobDefinition)).description
            files = list(session.scalars(select(Source).where(Source.original_stored)))
            originals = {
                str(row.id): document_store(remote).get(row.object_key) for row in files
            }
            session.add(
                OwnerSession(
                    id=identity,
                    owner_id=1,
                    expires_at=datetime.now(UTC) + timedelta(minutes=30),
                )
            )
        signed = (
            TimestampSigner(local.session_secret.get_secret_value())
            .sign(base64.b64encode(json.dumps({"id": str(identity)}).encode()))
            .decode()
        )
        with httpx2.Client(
            base_url=url, cookies={"career_session": signed}, timeout=30
        ) as client:
            stage = "authenticated API and original downloads"
            assert client.get("/api/session").status_code == 200
            before = client.get("/api/job-definition").json()
            assert before["description"] == description
            for source_id, content in originals.items():
                response = client.get(
                    f"/api/job-definition/sources/{source_id}/original"
                )
                assert response.status_code == 200 and response.content == content
            report["authenticated_api_and_original_downloads"] = True
            stage = "exact-origin protection"
            assert (
                client.put(
                    "/api/job-definition",
                    json={},
                    headers={"Origin": "https://untrusted.invalid"},
                ).status_code
                == 403
            )
            report["untrusted_origin_rejected"] = True
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context()
                context.add_cookies(
                    [
                        {
                            "name": "career_session",
                            "value": signed,
                            "url": url,
                            "httpOnly": True,
                            "secure": True,
                            "sameSite": "Strict",
                        }
                    ]
                )
                page = context.new_page()
                errors, ai_calls = [], []
                page.on("pageerror", lambda error: errors.append(type(error).__name__))
                page.on(
                    "request",
                    lambda req: (
                        ai_calls.append(req.url)
                        if req.method == "POST"
                        and any(
                            path in req.url
                            for path in ("/chat", "/clarifications", "/facts")
                        )
                        else None
                    ),
                )
                stage = "saved-data hydration"
                page.goto(url)
                editor = page.get_by_role(
                    "textbox", name="The role you’re looking for", exact=True
                )
                expect(editor).to_have_value(description, timeout=15000)
                stage = "floating assistant across all workflow steps"
                navigation = page.get_by_role("navigation", name="Definition steps")
                steps = navigation.get_by_role("button")
                for index in range(steps.count()):
                    steps.nth(index).click()
                    assert page.get_by_role(
                        "button", name="Chat with assistant", exact=True
                    ).is_visible()
                page.get_by_role(
                    "button", name="Chat with assistant", exact=True
                ).click()
                draft = page.get_by_label("Your message", exact=True)
                draft.fill("Unsent deployment verification draft")
                page.get_by_role(
                    "button", name="Minimize assistant", exact=True
                ).click()
                steps.nth(0).click()
                page.get_by_role(
                    "button", name="Chat with assistant", exact=True
                ).click()
                assert draft.input_value() == "Unsent deployment verification draft"
                page.get_by_role(
                    "button", name="Minimize assistant", exact=True
                ).click()
                stage = "language switching and persistence"
                page.locator(".locale-switcher select").select_option("es")
                expect(
                    page.get_by_role(
                        "button", name="Hablar con el asistente", exact=True
                    )
                ).to_be_visible()
                page.reload()
                expect(
                    page.get_by_role(
                        "button", name="Hablar con el asistente", exact=True
                    )
                ).to_be_visible()
                assert page.locator(".locale-switcher select").input_value() == "es"
                assert not errors and not ai_calls
                context.close()
                browser.close()
            report.update(
                bilingual_ui_and_language_persistence=True,
                floating_assistant_available_in_all_steps=True,
                unsent_chat_draft_survives_minimize_and_navigation=True,
                no_automatic_ai_calls=True,
            )
            stage = "unchanged saved workspace"
            assert client.get("/api/job-definition").json() == before
            report["saved_workspace_unchanged"] = True
            stage = "cookie security and session revocation"
            response = client.delete("/api/session", headers={"Origin": url})
            assert response.status_code == 204
            cookie = response.headers.get("set-cookie", "").lower()
            assert all(
                value in cookie for value in ("secure", "httponly", "samesite=strict")
            )
            assert client.get("/api/job-definition").status_code == 401
            report["secure_httponly_strict_cookies_and_revocation"] = True
        report["passed"] = True
        Path("doc/operations/evidence/PART11_DEPLOYED_CHECK.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(json.dumps(report))
    except Exception as error:
        path = Path(".cache/render-setup/deployed-check-error.log")
        path.write_text(traceback.format_exc())
        path.chmod(0o600)
        print(
            json.dumps(
                {"passed": False, "stage": stage, "error_type": type(error).__name__}
            )
        )
        raise SystemExit(1) from None
    finally:
        with sessions.begin() as session:
            session.execute(delete(OwnerSession).where(OwnerSession.id == identity))
        engine.dispose()


if __name__ == "__main__":
    main()
