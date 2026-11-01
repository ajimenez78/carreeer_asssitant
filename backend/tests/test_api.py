from fastapi.testclient import TestClient

from career_assistant.config import Settings
from career_assistant.main import create_app


def test_health_is_a_sanitized_liveness_probe():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_packaged_example_page_is_served_as_html():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Hello, world!" in response.text


def test_application_uses_configured_name():
    with TestClient(
        create_app(Settings(app_name="Local test application", _env_file=None))
    ) as client:
        schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Local test application"
    assert "/api/health" in schema["paths"]
