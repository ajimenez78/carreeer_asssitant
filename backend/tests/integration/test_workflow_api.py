from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.exc import OperationalError

from career_assistant.ai import AIError, AIResult, Usage
from career_assistant.ai_evaluation import REFERENCE_DESCRIPTION
from career_assistant.auth import PASSWORDS
from career_assistant.config import Settings
from career_assistant.db_cli import main
from career_assistant.errors import AppError
from career_assistant.main import create_app
from career_assistant.models import Owner, OwnerSession, Source
from career_assistant.persistence import DefinitionRepository
from career_assistant.storage import LocalDocumentStore
from career_assistant.workflow import ExtractedBackground

ROOT = "/api/job-definition"
ORIGIN = "http://testserver"
PASSWORD = "synthetic-test-password"


def criterion(
    key="seniority", category="seniority", value="Staff", priority="mandatory"
):
    return {
        "key": key,
        "category": category,
        "priority": priority,
        "value": value,
        "note": None,
    }


class FakeAI:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.callback = None
        self.proposal = {
            "preferences": [criterion()],
            "questions": [
                "What compensation range, currency, period and gross/net basis?",
                "Which period covers the on-site day limit?",
            ],
            "conflicts": [],
        }
        self.background = {
            "facts": [
                {
                    "content": "Historical frontend experience",
                    "evidence": "Historical frontend",
                }
            ],
            "unknowns": ["Education"],
        }

    def complete(self, *, instructions, data, response_type):
        self.calls.append(
            {"instructions": instructions, "data": data, "response_type": response_type}
        )
        if self.callback:
            self.callback()
        if self.failure:
            raise self.failure
        value = (
            self.background if response_type == ExtractedBackground else self.proposal
        )
        return AIResult(
            response_type.model_validate(value), "gpt-6-luna", Usage(100, 0, 50, 0), 0.1
        )


@pytest.fixture
def api(sessions, tmp_path):
    with sessions.begin() as session:
        owner = session.get(Owner, 1)
        owner.password_hash = PASSWORDS.hash(PASSWORD)
    ai = FakeAI()
    store = LocalDocumentStore(tmp_path / "originals")
    app = create_app(
        Settings(_env_file=None, session_secret="x" * 48, allowed_origins=[ORIGIN]),
        sessions=sessions,
        ai_client=ai,
        store=store,
    )
    with TestClient(app, headers={"Origin": ORIGIN}) as client:
        assert (
            client.post(
                "/api/session", json={"username": "owner", "password": PASSWORD}
            ).status_code
            == 200
        )
        yield client, ai, store, app


def save(client, **changes):
    response = client.put(ROOT, json={"description": REFERENCE_DESCRIPTION, **changes})
    assert response.status_code == 200, response.text
    return response.json()


def source(client, text="Historical frontend experience. Education not provided."):
    response = client.post(
        ROOT + "/sources",
        json={"kind": "text", "display_name": "Synthetic background", "text": text},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_full_flow_creates_reviews_clarifies_saves_reloads_and_refines(api):
    client, ai, store, app = api
    assert client.get(ROOT).status_code == 404
    initial = save(client)
    identity = initial["id"]
    assert initial["preferences"] == [] and initial["state"] == "draft"
    row = source(client)
    sid = row["id"]
    assert row["reviewed_at"] is None
    facts = client.post(f"{ROOT}/sources/{sid}/facts", json={"language": "Spanish"})
    assert facts.status_code == 200
    assert facts.json()["proposal"]["facts"][0]["evidence"] == "Historical frontend"
    assert client.get(f"{ROOT}/sources/{sid}").json()["facts"] == []
    unreviewed = client.post(ROOT + "/clarifications", json={})
    assert unreviewed.status_code == 200
    assert ai.calls[-1]["data"]["reviewed_background"] == []
    review = client.patch(
        f"{ROOT}/sources/{sid}",
        json={"facts": ["Corrected historical frontend experience"]},
    )
    assert review.status_code == 200
    assert review.json()["facts"][0]["source_id"] == sid
    assert client.get(ROOT).json()["clarifications"] == []
    response = client.post(ROOT + "/clarifications", json={"language": "Spanish"})
    assert response.status_code == 200, response.text
    proposal = response.json()
    assert ai.calls[-1]["data"]["language"] == "Spanish"
    assert ai.calls[-1]["data"]["reviewed_background"] == [
        {"source_id": sid, "content": "Corrected historical frontend experience"}
    ]
    assert "extracted_text" not in str(ai.calls[-1]["data"])
    assert client.get(ROOT).json()["preferences"] == []
    saved = save(
        client,
        preferences=proposal["proposal"]["preferences"],
        proposal_context=proposal["proposal_context"],
    )
    assert saved["id"] == identity
    assert saved["preferences"] == [criterion()]
    question = saved["clarifications"][0]
    answer = client.patch(
        f"{ROOT}/clarifications/{question['id']}", json={"state": "unknown"}
    )
    assert answer.status_code == 200
    other = saved["clarifications"][1]
    assert (
        client.patch(
            f"{ROOT}/clarifications/{other['id']}",
            json={"state": "answered", "answer": "2 days per week"},
        ).status_code
        == 200
    )
    save(
        client,
        description="Quiero un puesto Staff con arquitectura.",
        preferences=[criterion()],
        state="ready",
    )
    # A fresh application instance uses the same durable database/session.
    restarted = create_app(
        app.state.settings, sessions=app.state.sessions, ai_client=ai, store=store
    )
    with TestClient(
        restarted, headers={"Origin": ORIGIN}, cookies=dict(client.cookies)
    ) as reopened:
        loaded = reopened.get(ROOT).json()
        assert loaded["id"] == identity and loaded["state"] == "ready"
        assert loaded["sources"][0]["id"] == sid
        assert [row["answer_state"] for row in loaded["clarifications"]] == [
            "unknown",
            "answered",
        ]


def test_reference_proposal_preserves_constraints_and_explicit_unknowns(api):
    client, ai, *_ = api
    ai.proposal["preferences"] = [
        criterion(),
        criterion("architecture", "responsibilities", "Architecture and system design"),
        criterion("cross_team", "responsibilities", "Cross-team collaboration"),
        criterion("learning", "work_life_balance", "Continuous learning", "preferred"),
        criterion(
            "international_scope", "company_context", "International", "preferred"
        ),
        criterion(
            "ai_engineering", "technical_interests", "AI engineering", "preferred"
        ),
        criterion("remote", "work_arrangement", "Remote", "preferred"),
        criterion("hybrid_location", "location", "Madrid or nearby, for hybrid"),
        criterion("onsite_limit", "work_arrangement", {"days": 2, "period": None}),
        criterion("frontend_only", "responsibilities", "Frontend-only", "excluded"),
        criterion(
            "salary",
            "compensation",
            {
                "minimum": None,
                "maximum": None,
                "target": None,
                "currency": None,
                "period": None,
                "basis": None,
            },
            "preferred",
        ),
    ]
    save(client)
    sid = source(client)["id"]
    client.patch(
        f"{ROOT}/sources/{sid}", json={"facts": ["Historical frontend and SQL skills"]}
    )
    response = client.post(ROOT + "/clarifications", json={})
    assert response.status_code == 200, response.text
    data = response.json()
    prefs = {row["key"]: row for row in data["proposal"]["preferences"]}
    assert prefs["seniority"]["value"] == "Staff"
    assert prefs["hybrid_location"]["priority"] == "mandatory"
    assert prefs["onsite_limit"]["value"] == {"days": 2, "period": None}
    assert prefs["frontend_only"]["priority"] == "excluded"
    assert prefs["salary"]["value"]["minimum"] is None
    assert "sql" not in prefs
    assert len(data["clarifications"]) == 2
    assert "compensation" in data["clarifications"][0]["question"]
    prompt = ai.calls[-1]["instructions"]
    assert "mandatory" in prompt and "Source facts" in prompt
    assert "salary" not in str(client.get(ROOT).json()["preferences"])


@pytest.mark.parametrize("state", ["skipped", "unknown"])
def test_answer_states_survive_ai_failure_and_are_forwarded_without_guesses(api, state):
    client, ai, *_ = api
    save(client)
    question = client.post(ROOT + "/clarifications", json={}).json()["clarifications"][
        0
    ]
    assert (
        client.patch(
            f"{ROOT}/clarifications/{question['id']}", json={"state": state}
        ).status_code
        == 200
    )
    ai.failure = AIError("ai_timeout", "Timed out. Retry later.", 504)
    failed = client.post(ROOT + "/clarifications", json={})
    assert failed.status_code == 504
    assert ai.calls[-1]["data"]["clarifications"][0]["answer_state"] == state
    loaded = client.get(ROOT).json()
    assert loaded["description"] == REFERENCE_DESCRIPTION
    assert loaded["clarifications"][0]["answer"] is None
    assert loaded["preferences"] == []


def test_conflicting_proposal_keeps_omitted_accepted_preferences_until_explicit_save(
    api,
):
    client, ai, *_ = api
    accepted = [
        criterion(),
        criterion("remote", "work_arrangement", "Remote", "preferred"),
    ]
    save(client, preferences=accepted)
    ai.proposal["preferences"] = [criterion(value="Principal")]
    data = client.post(ROOT + "/clarifications", json={}).json()
    assert len(data["proposal"]["preferences"]) == 2
    assert data["proposal"]["conflicts"]
    assert client.get(ROOT).json()["preferences"] == sorted(
        accepted, key=lambda item: item["key"]
    )


def test_semantically_invalid_ai_output_and_unsupported_evidence_do_not_persist(api):
    client, ai, *_ = api
    saved = save(client, preferences=[criterion()])
    ai.proposal["preferences"] = [criterion(), criterion()]
    response = client.post(ROOT + "/clarifications", json={})
    assert response.status_code == 502
    assert client.get(ROOT).json() == saved
    ai.proposal["preferences"] = [
        criterion("salary", "compensation", "invented salary")
    ]
    assert client.post(ROOT + "/clarifications", json={}).status_code == 502
    sid = source(client)["id"]
    ai.background["facts"][0]["evidence"] = "nonexistent quote"
    assert client.post(f"{ROOT}/sources/{sid}/facts", json={}).status_code == 502
    assert client.get(f"{ROOT}/sources/{sid}").json()["reviewed_at"] is None


def test_stale_inflight_and_reviewed_proposals_are_rejected(api, sessions):
    client, ai, *_ = api
    save(client)
    data = client.post(ROOT + "/clarifications", json={}).json()
    save(client, description="Changed manually")
    response = client.put(
        ROOT,
        json={
            "description": REFERENCE_DESCRIPTION,
            "preferences": data["proposal"]["preferences"],
            "proposal_context": data["proposal_context"],
        },
    )
    assert response.status_code == 409

    def mutate():
        with sessions.begin() as session:
            DefinitionRepository(session).current(
                lock=True
            ).description = "Changed during AI call"

    ai.callback = mutate
    assert client.post(ROOT + "/clarifications", json={}).status_code == 409
    assert client.get(ROOT).json()["description"] == "Changed during AI call"


def test_failed_commit_rolls_back_definition_and_preferences(api, database):
    client, *_ = api
    saved = save(client, preferences=[criterion()])

    def fail_commit(connection):
        raise OperationalError(
            "synthetic personal text", None, Exception("private provider detail")
        )

    event.listen(database, "commit", fail_commit)
    try:
        response = client.put(
            ROOT, json={"description": "uncommitted private input", "preferences": []}
        )
    finally:
        event.remove(database, "commit", fail_commit)
    assert response.status_code == 503
    assert "private" not in response.text
    assert client.get(ROOT).json() == saved


@pytest.mark.parametrize(
    "filename", ["synthetic.pdf", "synthetic.docx", "synthetic.md", "synthetic.doc"]
)
def test_document_uploads_private_original_download_and_extraction(
    api, filename, pdf_bytes, docx_bytes
):
    from pathlib import Path

    client, *_ = api
    save(client)
    content = {
        "synthetic.pdf": pdf_bytes(),
        "synthetic.docx": docx_bytes(),
        "synthetic.md": b"Synthetic Staff engineer",
        "synthetic.doc": (
            Path(__file__).parents[1] / "fixtures" / "synthetic.doc"
        ).read_bytes(),
    }[filename]
    response = client.post(
        ROOT + "/sources",
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == 201, response.text
    row = response.json()
    assert row["extraction_state"] == "ready" and row["original_stored"]
    assert row["reviewed_at"] is None and "Staff engineer" in row["extracted_text"]
    original = client.get(f"{ROOT}/sources/{row['id']}/original")
    assert original.content == content
    assert original.headers["content-disposition"] == "attachment"
    assert "no-store" in original.headers["cache-control"]


def test_file_limit_failures_are_recoverable_and_unsupported_uploads_are_rejected(
    api, pdf_bytes
):
    client, ai, *_ = api
    save(client)
    assert (
        client.post(ROOT + "/sources", files={"file": ("a.exe", b"bad")}).status_code
        == 415
    )
    assert (
        client.post(ROOT + "/sources", files={"file": ("a.pdf", b"")}).status_code
        == 422
    )
    assert (
        client.post(
            ROOT + "/sources", files={"file": ("a.md", b"x" * (10 * 1024 * 1024 + 1))}
        ).status_code
        == 413
    )
    failed = client.post(
        ROOT + "/sources", files={"file": ("a.pdf", b"bad pdf")}
    ).json()
    assert failed["extraction_state"] == "failed" and failed["original_stored"]
    assert failed["extraction_error"]["code"] == "invalid_document"
    sid = failed["id"]
    assert (
        client.patch(f"{ROOT}/sources/{sid}", json={"facts": ["invented"]}).status_code
        == 409
    )
    assert client.post(f"{ROOT}/sources/{sid}/facts", json={}).status_code == 409
    assert (
        client.post(f"{ROOT}/sources/{sid}/retry").json()["extraction_state"]
        == "failed"
    )
    for index in range(4):
        assert (
            client.post(
                ROOT + "/sources", files={"file": (f"{index}.md", b"Synthetic text")}
            ).status_code
            == 201
        )
    assert (
        client.post(
            ROOT + "/sources", files={"file": ("six.md", b"Synthetic text")}
        ).status_code
        == 422
    )
    assert client.delete(f"{ROOT}/sources/{sid}").status_code == 200
    assert (
        client.post(
            ROOT + "/sources", files={"file": ("replacement.md", b"text")}
        ).status_code
        == 201
    )


def test_url_failure_retains_provenance_and_paste_fallback(api):
    client, ai, store, app = api
    save(client)

    class Processor:
        def fetch(self, url):
            raise AppError(
                "source_unavailable",
                "Page restricted. Upload a document or paste text.",
                422,
            )

    app.state.processor = Processor()
    response = client.post(
        ROOT + "/sources",
        json={
            "kind": "url",
            "display_name": "LinkedIn",
            "url": "https://www.linkedin.com/in/synthetic",
        },
    )
    assert response.status_code == 201
    row = response.json()
    assert row["extraction_state"] == "failed" and row["url"].startswith("https://")
    assert "paste" in row["extraction_error"]["message"]
    app.state.processor.fetch = lambda url: "Public synthetic profile"
    assert (
        client.post(f"{ROOT}/sources/{row['id']}/retry").json()["extraction_state"]
        == "ready"
    )
    pasted = source(client, "Pasted synthetic profile")
    assert pasted["extraction_state"] == "ready"
    assert client.post(f"{ROOT}/sources/{pasted['id']}/retry").status_code == 409


def test_source_deletion_removes_future_context_but_retains_accepted_preferences(api):
    client, ai, *_ = api
    save(client, preferences=[criterion()])
    sid = source(client, "Deleted source marker")["id"]
    client.patch(f"{ROOT}/sources/{sid}", json={"facts": ["Deleted source marker"]})
    client.post(ROOT + "/clarifications", json={})
    assert "Deleted source marker" in str(ai.calls[-1]["data"])
    assert client.delete(f"{ROOT}/sources/{sid}").json()["cleanup_pending"] is False
    loaded = client.get(ROOT).json()
    assert loaded["sources"] == [] and loaded["clarifications"] == []
    assert loaded["preferences"] == [criterion()]
    client.post(ROOT + "/clarifications", json={})
    assert "Deleted source marker" not in str(ai.calls[-1]["data"])
    assert client.get(f"{ROOT}/sources/{sid}").status_code == 404


def test_storage_failures_keep_reserved_keys_and_deletion_queue_for_retry(
    api, monkeypatch, sessions
):
    client, ai, store, app = api
    save(client)
    original_put = store.put
    monkeypatch.setattr(
        store,
        "put",
        lambda *args: (_ for _ in ()).throw(
            OSError("private internal storage failure")
        ),
    )
    response = client.post(
        ROOT + "/sources", files={"file": ("a.md", b"Synthetic text")}
    )
    assert response.status_code == 503
    sid = response.json()["error"]["fields"]["source_id"]
    row = client.get(f"{ROOT}/sources/{sid}").json()
    assert row["extraction_state"] == "failed" and row["original_stored"] is False
    assert "private internal" not in response.text
    with sessions() as session:
        key = session.get(Source, UUID(sid)).object_key
    original_put(key, b"Synthetic text")
    assert (
        client.post(f"{ROOT}/sources/{sid}/retry").json()["extraction_state"] == "ready"
    )
    original_delete = store.delete
    monkeypatch.setattr(
        store, "delete", lambda *args: (_ for _ in ()).throw(OSError("outage"))
    )
    result = client.delete(ROOT).json()
    assert result == {"cleanup_pending": True, "pending_originals": 1}
    assert client.get(ROOT).status_code == 404
    assert client.get(f"{ROOT}/sources/{sid}/original").status_code == 404
    monkeypatch.setattr(store, "delete", original_delete)
    assert client.post(ROOT + "/cleanup").json()["cleanup_pending"] is False
    with pytest.raises(FileNotFoundError):
        store.get(key)
    assert client.get("/api/session").status_code == 200


def test_failed_retry_of_reviewed_file_clears_derived_context(api, monkeypatch):
    client, ai, store, app = api
    save(client, preferences=[criterion()])
    row = client.post(
        ROOT + "/sources", files={"file": ("a.md", b"Historical frontend")}
    ).json()
    sid = row["id"]
    client.patch(f"{ROOT}/sources/{sid}", json={"facts": ["Historical frontend"]})
    client.post(ROOT + "/clarifications", json={})
    monkeypatch.setattr(
        store, "get", lambda *args: (_ for _ in ()).throw(OSError("outage"))
    )
    assert client.post(f"{ROOT}/sources/{sid}/retry").status_code == 503
    loaded = client.get(f"{ROOT}/sources/{sid}").json()
    assert loaded["extraction_state"] == "failed"
    assert loaded["facts"] == [] and loaded["reviewed_at"] is None
    definition = client.get(ROOT).json()
    assert definition["clarifications"] == []
    assert definition["preferences"] == [criterion()]


def test_invalid_inputs_have_content_free_actionable_errors(api):
    client, *_ = api
    save(client)
    for body in [
        {"description": " "},
        {
            "description": "x",
            "preferences": [
                criterion("salary", "compensation", {"minimum": 10, "maximum": 1})
            ],
        },
        {"description": "x", "unexpected": "secret"},
    ]:
        response = client.put(ROOT, json=body)
        assert response.status_code == 422
        assert response.json()["error"]["fields"]
        assert "secret" not in response.text
    sid = source(client)["id"]
    assert (
        client.patch(f"{ROOT}/sources/{sid}", json={"facts": [" "]}).status_code == 422
    )
    assert (
        client.post(
            ROOT + "/sources",
            json={
                "kind": "url",
                "display_name": "Invalid",
                "url": "file:///etc/passwd",
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            ROOT + "/sources",
            content=b"invalid JSON",
            headers={"Content-Type": "application/json"},
        ).status_code
        == 422
    )
    assert client.post(ROOT + "/sources", content=b"text").status_code == 415
    assert client.get(ROOT + "/sources/not-a-uuid").status_code == 422
    assert client.get(f"{ROOT}/sources/{uuid4()}").status_code == 404


def test_invalid_storage_configuration_retains_recoverable_source(api):
    client, ai, store, app = api
    save(client)
    app.state.store = None
    app.state.settings.document_backend = "neon"
    response = client.post(ROOT + "/sources", files={"file": ("a.md", b"Synthetic")})
    assert response.status_code == 503
    sid = response.json()["error"]["fields"]["source_id"]
    assert client.get(f"{ROOT}/sources/{sid}").json()["extraction_state"] == "failed"
    assert client.delete(f"{ROOT}/sources/{sid}").json()["cleanup_pending"]
    app.state.store = store
    assert not client.post(ROOT + "/cleanup").json()["cleanup_pending"]


def test_unconfigured_owner_and_secure_cookie_boundary(api, sessions):
    client, ai, store, app = api
    origin = "https://testserver"
    secure_app = create_app(
        Settings(
            _env_file=None,
            session_secret="x" * 48,
            session_secure=True,
            allowed_origins=[origin],
        ),
        sessions=sessions,
        store=store,
        ai_client=ai,
    )
    with TestClient(secure_app, base_url=origin, headers={"Origin": origin}) as browser:
        response = browser.post(
            "/api/session", json={"username": "owner", "password": PASSWORD}
        )
        assert response.status_code == 200
        assert "secure" in response.headers["set-cookie"].lower()
        assert (
            browser.get(
                ROOT, headers={"Cookie": "career_session=tampered.signature"}
            ).status_code
            == 401
        )
        with sessions.begin() as session:
            session.get(Owner, 1).password_hash = None
        response = browser.post(
            "/api/session", json={"username": "owner", "password": PASSWORD}
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "login_not_configured"


def test_login_private_access_cookie_security_origin_protection_and_logout(api):
    client, ai, store, app = api
    save(client)
    sid = source(client)["id"]
    with TestClient(app) as anonymous:
        for method, path in [
            ("get", ROOT),
            ("put", ROOT),
            ("get", f"{ROOT}/sources/{sid}"),
            ("get", f"{ROOT}/sources/{sid}/original"),
            ("post", ROOT + "/clarifications"),
        ]:
            kwargs = (
                {"json": {"description": "private"}}
                if method == "put"
                else {"json": {}}
                if method == "post"
                else {}
            )
            response = getattr(anonymous, method)(
                path, headers={"Origin": ORIGIN}, **kwargs
            )
            assert response.status_code == 401
        assert (
            anonymous.post(
                "/api/session", json={"username": "owner", "password": PASSWORD}
            ).status_code
            == 403
        )
        assert (
            anonymous.post(
                "/api/session",
                headers={"Origin": "https://attacker.invalid"},
                json={"username": "owner", "password": PASSWORD},
            ).status_code
            == 403
        )
        login = anonymous.post(
            "/api/session",
            headers={"Origin": ORIGIN},
            json={"username": "owner", "password": PASSWORD},
        )
        assert login.status_code == 200
        assert "httponly" in login.headers["set-cookie"].lower()
        assert "samesite=strict" in login.headers["set-cookie"].lower()
        captured = anonymous.cookies.get("career_session")
        assert (
            anonymous.delete("/api/session", headers={"Origin": ORIGIN}).status_code
            == 204
        )
        anonymous.cookies.set("career_session", captured)
        assert anonymous.get(ROOT).status_code == 401


def test_login_throttle_expiration_and_owner_reconfiguration(
    api, sessions, monkeypatch, capsys
):
    client, ai, store, app = api
    for _ in range(5):
        assert (
            client.post(
                "/api/session", json={"username": "owner", "password": "incorrect"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/session", json={"username": "owner", "password": PASSWORD}
        ).status_code
        == 429
    )
    with sessions.begin() as session:
        session.get(Owner, 1).locked_until = datetime.now(UTC) - timedelta(seconds=1)
    assert (
        client.post(
            "/api/session", json={"username": "owner", "password": PASSWORD}
        ).status_code
        == 200
    )
    with sessions.begin() as session:
        for row in session.scalars(select(OwnerSession)):
            row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert client.get(ROOT).status_code == 401
    monkeypatch.setenv(
        "DATABASE_URL", sessions.kw["bind"].url.render_as_string(hide_password=False)
    )
    monkeypatch.setattr("getpass.getpass", lambda prompt: "new-synthetic-password")
    main(["owner", "--username", "private-owner"])
    assert "previous sessions revoked" in capsys.readouterr().out
    with sessions() as session:
        assert session.get(Owner, 1).username == "private-owner"
        assert PASSWORDS.verify(
            "new-synthetic-password", session.get(Owner, 1).password_hash
        )
    assert (
        client.post(
            "/api/session",
            json={"username": "private-owner", "password": "new-synthetic-password"},
        ).status_code
        == 200
    )
