from fastapi.testclient import TestClient

from career_assistant.config import Settings
from career_assistant.main import create_app


def test_health_is_a_sanitized_liveness_probe():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_static_export_and_api_routes_remain_separate(tmp_path):
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<h1>Clarify your next role</h1>")
    (frontend / "app.js").write_text("console.log('synthetic asset')")
    (tmp_path / "secret.txt").write_text("private-original")
    with TestClient(
        create_app(Settings(_env_file=None, frontend_directory=frontend))
    ) as client:
        response = client.get("/")
        assert client.get("/app.js").status_code == 200
        missing = client.get("/api/not-a-route")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "not_found"
        assert client.get("/..%2Fsecret.txt").status_code == 404
        assert "private-original" not in client.get("/secret.txt").text

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Clarify your next role" in response.text


def test_credentialed_cors_and_errors_keep_exact_origin_boundaries():
    origin = "http://127.0.0.1:3000"
    with TestClient(
        create_app(Settings(_env_file=None, allowed_origins=[origin]))
    ) as client:
        response = client.options(
            "/api/session",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
        invalid = client.options(
            "/api/session",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert invalid.status_code == 400
        assert "access-control-allow-origin" not in invalid.headers
        unauthenticated = client.get("/api/session", headers={"Origin": origin})
        assert unauthenticated.status_code == 401
        assert unauthenticated.headers["access-control-allow-origin"] == origin
        assert unauthenticated.headers["cache-control"] == "no-store"
        rejected = client.post("/api/session", json={})
        assert rejected.status_code == 403


def test_application_uses_configured_name():
    with TestClient(
        create_app(Settings(app_name="Local test application", _env_file=None))
    ) as client:
        schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Local test application"
    assert "/api/health" in schema["paths"]


def test_missing_login_secret_gives_setup_guidance_without_opening_database():
    with TestClient(
        create_app(Settings(_env_file=None, session_secret=None))
    ) as client:
        response = client.post(
            "/api/session",
            headers={"Origin": "http://127.0.0.1:8000"},
            json={"username": "owner", "password": "synthetic-password"},
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "login_not_configured"
