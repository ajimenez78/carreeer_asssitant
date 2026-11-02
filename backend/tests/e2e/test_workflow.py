from datetime import UTC, datetime, timedelta
from threading import Event
from time import monotonic

from playwright.sync_api import expect
from sqlalchemy import update
from workflow_fixtures import BACKGROUND, PASSWORD

from career_assistant.ai_evaluation import REFERENCE_DESCRIPTION
from career_assistant.models import OwnerSession


def login(page, origin):
    page.goto(origin)
    page.get_by_label("Username", exact=True).fill("owner")
    page.get_by_label("Password", exact=True).fill(PASSWORD)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(
        page.get_by_role("heading", name="Clarify the role you’re looking for.")
    ).to_be_visible()


def step(page, name):
    page.get_by_role("navigation", name="Definition steps").get_by_role(
        "button", name=name
    ).click()


def description(page):
    return page.get_by_role("textbox", name="The role you’re looking for", exact=True)


def save_draft(page, text=REFERENCE_DESCRIPTION):
    description(page).fill(text)
    page.get_by_role("button", name="Save draft", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")


def test_system_assessment_summary_and_manual_edit_invalidation(page, workflow):
    origin, _, ai, _ = workflow
    login(page, origin)
    save_draft(page)
    step(page, "03 Clarify")
    page.get_by_role(
        "button", name="Request clarification & suggestions", exact=True
    ).click()
    expect(page.locator(".save-summary")).to_contain_text("Needs clarification")
    initial = page.request.get(origin + "/api/job-definition").json()
    assert initial["state"] == "draft"
    assert initial["assessment"]["sufficient"] is False
    step(page, "05 Summary")
    summary = page.get_by_role("article", name="Saved role summary")
    expect(summary).to_contain_text("You are looking for a Staff engineering role")
    expect(page.get_by_text("Office-day period", exact=True)).to_be_visible()
    expect(
        page.get_by_text(
            "This view describes your saved definition. Unsaved edits and proposed "
            "criteria are not included until you review and save them."
        )
    ).to_be_visible()
    step(page, "04 Review & save")
    page.get_by_role("button", name="Apply reviewed suggestions & save").click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    saved = page.request.get(origin + "/api/job-definition").json()
    assert saved["state"] == "draft" and saved["assessment"] is None

    ai.sufficient = True
    step(page, "03 Clarify")
    page.get_by_label("Assistance language").select_option("Spanish")
    page.get_by_role(
        "button", name="Request clarification & suggestions", exact=True
    ).click()
    expect(page.locator(".save-summary")).to_contain_text("Sufficiently clear")
    assessed = page.request.get(origin + "/api/job-definition").json()
    assert assessed["state"] == "ready"
    assert assessed["assessment"]["sufficient"] is True
    assert assessed["assessment"]["language"] == "Spanish"
    step(page, "04 Review & save")
    page.get_by_role("button", name="Discard suggestions", exact=True).click()
    page.reload()
    step(page, "05 Summary")
    expect(summary).to_contain_text("Buscas un puesto de ingeniería Staff")
    expect(summary.locator(".summary-prose")).to_have_attribute("lang", "es")
    expect(page.locator(".save-summary")).to_contain_text("Sufficiently clear")
    expect(page.get_by_label("Definition status", exact=True)).to_have_count(0)

    step(page, "01 Describe")
    revised = REFERENCE_DESCRIPTION + " A four-day working week is preferred."
    description(page).fill(revised)
    page.get_by_role("button", name="Save draft", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    edited = page.request.get(origin + "/api/job-definition").json()
    assert edited["state"] == "draft" and edited["assessment"] is None
    expect(page.locator(".save-summary")).to_contain_text("Not assessed yet")
    step(page, "05 Summary")
    expect(summary).to_have_count(0)
    expect(
        page.get_by_role("button", name="Assess clarity & update summary")
    ).to_be_enabled()


def test_stop_during_real_inference_rejects_late_result(page, workflow, monkeypatch):
    origin, app, ai, _ = workflow
    started, release, completed = Event(), Event(), Event()
    calls = []
    original_complete = ai.complete

    def deferred_complete(**kwargs):
        calls.append(kwargs["data"]["language"])
        started.set()
        assert release.wait(timeout=30), "Synthetic AI release was not signaled"
        return original_complete(**kwargs)

    monkeypatch.setattr(ai, "complete", deferred_complete)
    original_stack = app.middleware_stack
    assert original_stack is not None

    async def observe_completion(scope, receive, send):
        try:
            await original_stack(scope, receive, send)
        finally:
            if (
                scope["type"] == "http"
                and scope["path"] == "/api/job-definition/clarifications"
                and scope["method"] == "POST"
            ):
                completed.set()

    monkeypatch.setattr(app, "middleware_stack", observe_completion)
    try:
        login(page, origin)
        save_draft(page)
        step(page, "03 Clarify")
        page.get_by_role(
            "button", name="Request clarification & suggestions", exact=True
        ).click()
        assert started.wait(timeout=5), "Synthetic AI call did not start"
        stop = page.get_by_role("button", name="Stop clarification", exact=True)
        expect(stop).to_be_enabled()
        stop.click()
        expect(page.get_by_role("status")).to_contain_text("Clarification stopped")
        release.set()
        assert completed.wait(timeout=5), "Canceled AI request did not finish"
        record = page.request.get(origin + "/api/job-definition").json()
        assert record["clarification_paused"] is True
        assert record["assessment"] is None and record["clarifications"] == []
        expect(page.locator(".question-card")).to_have_count(0)
        expect(page.locator(".save-summary")).to_contain_text("Not assessed yet")

        page.reload()
        expect(description(page)).to_have_value(REFERENCE_DESCRIPTION)
        resume = page.get_by_role("button", name="Resume clarification", exact=True)
        expect(resume).to_be_visible()
        assert (
            page.request.get(origin + "/api/job-definition").json()[
                "clarification_paused"
            ]
            is True
        )
        resume.click()
        expect(page.get_by_role("status")).to_contain_text("Clarification resumed")
        resumed = page.request.get(origin + "/api/job-definition").json()
        assert resumed["clarification_paused"] is False
        assert resumed["assessment"] is None and resumed["clarifications"] == []
        assert calls == ["English"]
    finally:
        release.set()


def test_late_save_response_preserves_acknowledged_stop(page, workflow):
    origin, _, _, _ = workflow
    login(page, origin)
    save_draft(page)
    held = []
    endpoint = origin + "/api/job-definition"

    def defer_save_response(route):
        if route.request.method == "PUT":
            held.append((route, route.fetch()))
        else:
            route.continue_()

    page.route(endpoint, defer_save_response)
    revised = REFERENCE_DESCRIPTION + " A four-day working week is preferred."
    description(page).fill(revised)
    page.get_by_role("button", name="Save draft", exact=True).click()
    deadline = monotonic() + 5
    while not held and monotonic() < deadline:
        page.wait_for_timeout(10)
    assert len(held) == 1, "Successful save response was not held"
    route, response = held[0]
    assert response.ok and response.json()["clarification_paused"] is False
    page.get_by_role("button", name="Stop clarification", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Clarification stopped")
    assert page.request.get(endpoint).json()["clarification_paused"] is True
    route.fulfill(response=response)
    expect(description(page)).to_have_value(revised)
    expect(page.get_by_role("button", name="Resume clarification")).to_be_enabled()
    expect(page.get_by_role("button", name="Save draft", exact=True)).to_be_enabled()
    expect(page.locator(".save-summary")).to_contain_text("Clarification stopped")
    expect(page.locator(".save-summary")).to_contain_text(
        "All definition changes saved"
    )
    page.unroute(endpoint, defer_save_response)
    page.reload()
    expect(description(page)).to_have_value(revised)
    expect(page.get_by_role("button", name="Resume clarification")).to_be_enabled()


def test_real_browser_flow_and_application_restart(page, workflow, pdf_bytes, serve):
    origin, _, ai, factory = workflow
    errors = []
    page.on("pageerror", lambda e: errors.append(e.message))
    login(page, origin)
    save_draft(page)
    step(page, "02 Background")
    page.get_by_label("Document", exact=True).set_input_files(
        {
            "name": "synthetic-cv.pdf",
            "mimeType": "application/pdf",
            "buffer": pdf_bytes(BACKGROUND),
        }
    )
    page.get_by_role("button", name="Add source", exact=True).click()
    page.get_by_role("button", name="Suggest background facts", exact=True).click()
    page.get_by_label("Reviewed facts, one per line").fill(
        "Corrected historical Python experience"
    )
    page.get_by_role("button", name="Accept reviewed facts", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Background facts accepted")
    page.get_by_label("Source type").select_option("url")
    page.get_by_label("Source name").fill("Public profile")
    page.get_by_label("Public URL").fill("https://example.com/profile")
    page.get_by_role("button", name="Add source", exact=True).click()
    expect(
        page.get_by_role("button", name="Review Public profile", exact=True)
    ).to_be_visible()
    step(page, "03 Clarify")
    page.get_by_role(
        "button", name="Request clarification & suggestions", exact=True
    ).click()
    step(page, "04 Review & save")
    page.get_by_role("button", name="Apply reviewed suggestions & save").click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    saved = page.request.get(origin + "/api/job-definition").json()
    assert saved["preferences"] and len(saved["sources"]) == 2
    assert any(
        p["key"] == "salary" and p["value"] is None for p in saved["preferences"]
    )
    step(page, "03 Clarify")
    questions = page.locator(".question-card")
    questions.nth(0).get_by_role("textbox").fill("EUR 100,000 gross per year")
    questions.nth(0).get_by_role("button", name="Save answer", exact=True).click()
    questions.nth(1).get_by_role("button", name="Skip question", exact=True).click()
    questions.nth(2).get_by_role("button", name="I don’t know yet", exact=True).click()
    step(page, "04 Review & save")
    salary = page.locator(".criterion").filter(
        has=page.locator('input[value="salary"]')
    )
    salary.get_by_label("Value type").select_option("compensation")
    salary.get_by_label("Minimum", exact=True).fill("100000")
    salary.get_by_label("Currency", exact=True).fill("EUR")
    salary.get_by_label("Pay period").select_option("year")
    salary.get_by_label("Tax basis").select_option("gross")
    page.get_by_role("button", name="Save definition", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    page.reload()
    expect(description(page)).to_have_value(REFERENCE_DESCRIPTION)
    step(page, "04 Review & save")
    expect(salary.get_by_label("Minimum", exact=True)).to_have_value("100000")
    # New application lifecycle; retain DB, secret, and original storage.
    with serve(factory) as (restarted, _):
        page.goto(restarted)
        expect(description(page)).to_have_value(REFERENCE_DESCRIPTION)
        record = page.request.get(restarted + "/api/job-definition").json()
        assert record["id"] == saved["id"] and record["state"] == "draft"
        assert [q["answer_state"] for q in record["clarifications"]] == [
            "answered",
            "skipped",
            "unknown",
        ]
        sid = next(s["id"] for s in record["sources"] if s["kind"] == "file")
        original = page.request.get(
            restarted + f"/api/job-definition/sources/{sid}/original"
        )
        assert original.status == 200 and original.body().startswith(b"%PDF")
    assert not ai.failure and errors == []


def test_real_errors_session_expiry_and_source_deletion(page, workflow, sessions):
    origin, _, ai, _ = workflow
    login(page, origin)
    save_draft(page)
    step(page, "02 Background")
    page.get_by_label("Document", exact=True).set_input_files(
        {
            "name": "bad.exe",
            "mimeType": "application/octet-stream",
            "buffer": b"invalid",
        }
    )
    page.get_by_role("button", name="Add source", exact=True).click()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text("Markdown")
    expect(page.get_by_label("Document", exact=True)).to_have_value(
        "C:\\fakepath\\bad.exe"
    )
    page.get_by_label("Source type").select_option("url")
    page.get_by_label("Source name").fill("Restricted profile")
    page.get_by_label("Public URL").fill("https://restricted.example/profile")
    page.get_by_role("button", name="Add source", exact=True).click()
    expect(page.get_by_text("Extraction failed", exact=True)).to_be_visible()
    page.get_by_label("Source type").select_option("text")
    page.get_by_label("Source name").fill("Pasted profile")
    page.get_by_label("Background text").fill(BACKGROUND)
    page.get_by_role("button", name="Add source", exact=True).click()
    step(page, "03 Clarify")
    ai.failure = True
    page.get_by_role(
        "button", name="Request clarification & suggestions", exact=True
    ).click()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text("unavailable")
    ai.failure = False
    page.get_by_role(
        "button", name="Request clarification & suggestions", exact=True
    ).click()
    step(page, "04 Review & save")
    page.get_by_role("button", name="Apply reviewed suggestions & save").click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    before = page.request.get(origin + "/api/job-definition").json()["preferences"]
    step(page, "02 Background")
    page.get_by_role("button", name="Remove Pasted profile", exact=True).click()
    page.get_by_role("button", name="Confirm remove source", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Source removed")
    record = page.request.get(origin + "/api/job-definition").json()
    assert record["preferences"] == before and record["clarifications"] == []
    step(page, "01 Describe")
    description(page).fill("An unsaved refinement")
    with sessions.begin() as session:
        session.execute(
            update(OwnerSession).values(
                expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        )
    page.get_by_role("button", name="Save draft", exact=True).click()
    expect(
        page.get_by_role("heading", name="Sign in to your workspace.")
    ).to_be_visible()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text(
        "session expired"
    )
    page.get_by_label("Username", exact=True).fill("owner")
    page.get_by_label("Password", exact=True).fill(PASSWORD)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(description(page)).to_have_value("An unsaved refinement")
    assert (
        page.request.get(origin + "/api/job-definition").json()["description"]
        == REFERENCE_DESCRIPTION
    )
    page.get_by_role("button", name="Save draft", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(
        page.get_by_role("heading", name="Sign in to your workspace.")
    ).to_be_visible()
    assert page.request.get(origin + "/api/job-definition").status == 401


def test_pending_original_cleanup_is_visible_and_retryable(page, workflow, monkeypatch):
    origin, app, _, _ = workflow
    login(page, origin)
    save_draft(page, "An incomplete draft")
    step(page, "02 Background")
    page.get_by_label("Document", exact=True).set_input_files(
        {"name": "cv.md", "mimeType": "text/markdown", "buffer": BACKGROUND.encode()}
    )
    page.get_by_role("button", name="Add source", exact=True).click()
    original_delete = app.state.store.delete

    def unavailable(key):
        raise OSError("Synthetic private storage outage")

    monkeypatch.setattr(app.state.store, "delete", unavailable)
    page.get_by_role("button", name="Remove cv.md", exact=True).click()
    page.get_by_role("button", name="Confirm remove source", exact=True).click()
    expect(
        page.get_by_text(
            "Source records were removed, but original-file cleanup is still pending."
        )
    ).to_be_visible()
    assert page.request.get(origin + "/api/job-definition").json()["sources"] == []
    monkeypatch.setattr(app.state.store, "delete", original_delete)
    page.get_by_role("button", name="Retry original cleanup", exact=True).click()
    expect(
        page.get_by_text(
            "Source records were removed, but original-file cleanup is still pending."
        )
    ).to_have_count(0)


def test_cross_origin_browser_session_and_origin_rejection(page, workflow, serve):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    _, _, _, factory = workflow
    frontend = FastAPI()

    @frontend.get("/")
    def blank():
        return HTMLResponse("<h1>Synthetic development origin</h1>")

    with serve(lambda _: frontend) as (web_origin, _):
        with serve(lambda api_origin: factory(api_origin, (web_origin,))) as (
            origin,
            _,
        ):
            page.goto(web_origin)
            result = page.evaluate(
                """async ({origin, password}) => {
                  const credentials = {credentials: 'include'};
                  const headers = {'Content-Type': 'application/json'};
                  const login = await fetch(origin + '/api/session', {
                    ...credentials, method: 'POST', headers,
                    body: JSON.stringify({username:'owner', password})
                  });
                  const session = await fetch(origin + '/api/session', credentials);
                  const save = await fetch(origin + '/api/job-definition', {
                    ...credentials, method:'PUT', headers,
                    body:JSON.stringify({
                      description:'Cross-origin draft', state:'draft', preferences:[]
                    })
                  });
                  return [login.status, session.status, save.status];
                }""",
                {"origin": origin, "password": PASSWORD},
            )
            assert result == [200, 200, 200]
            rejected = page.request.post(
                origin + "/api/session",
                headers={"Origin": "https://untrusted.example"},
                data={"username": "owner", "password": PASSWORD},
            )
            assert rejected.status == 403


def test_reserved_source_is_visible_when_original_write_fails(
    page, workflow, monkeypatch
):
    origin, app, _, _ = workflow
    login(page, origin)
    save_draft(page, "An incomplete draft")
    step(page, "02 Background")
    page.get_by_label("Document", exact=True).set_input_files(
        {"name": "cv.md", "mimeType": "text/markdown", "buffer": BACKGROUND.encode()}
    )
    original_put = app.state.store.put

    def unavailable(key, content):
        raise OSError("Synthetic original write failure")

    monkeypatch.setattr(app.state.store, "put", unavailable)
    page.get_by_role("button", name="Add source", exact=True).click()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text(
        "Original storage failed"
    )
    expect(
        page.get_by_text(
            "There is no stored original. Remove this source and upload it again."
        )
    ).to_be_visible()
    expect(page.get_by_label("Document", exact=True)).to_have_value(
        "C:\\fakepath\\cv.md"
    )
    assert len(page.request.get(origin + "/api/job-definition").json()["sources"]) == 1
    monkeypatch.setattr(app.state.store, "put", original_put)
    page.get_by_role("button", name="Remove cv.md", exact=True).click()
    page.get_by_role("button", name="Confirm remove source", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Source removed")
    page.get_by_role("button", name="Add source", exact=True).click()
    expect(page.get_by_text("Ready for review", exact=True)).to_be_visible()


def test_real_spanish_sign_in_and_upload_errors(page, workflow):
    origin, _, _, _ = workflow
    page.goto(origin)
    page.locator(".locale-switcher select").select_option("es")
    page.get_by_label("Usuario", exact=True).fill("owner")
    page.get_by_label("Contraseña", exact=True).fill("incorrect-synthetic-password")
    page.get_by_role("button", name="Iniciar sesión", exact=True).click()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text(
        "El usuario o la contraseña son incorrectos"
    )
    expect(page.get_by_label("Contraseña", exact=True)).to_have_value("")
    page.get_by_label("Contraseña", exact=True).fill(PASSWORD)
    page.get_by_role("button", name="Iniciar sesión", exact=True).click()
    page.get_by_role("textbox", name="El puesto que buscas", exact=True).fill(
        "Un puesto con conciliación"
    )
    page.get_by_role("button", name="Guardar borrador", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Definición guardada")
    page.get_by_role("navigation", name="Pasos de la definición").get_by_role(
        "button", name="02 Trayectoria"
    ).click()
    page.get_by_label("Documento", exact=True).set_input_files(
        {
            "name": "bad.exe",
            "mimeType": "application/octet-stream",
            "buffer": b"invalid",
        }
    )
    page.get_by_role("button", name="Añadir fuente", exact=True).click()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text(
        "Sube un archivo PDF"
    )
