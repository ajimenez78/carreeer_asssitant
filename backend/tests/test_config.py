from career_assistant.config import Settings
from career_assistant.database import database_url
from career_assistant.storage import S3DocumentStore, document_store


def test_settings_load_backend_secrets_without_exposing_them(tmp_path):
    configuration = tmp_path / ".env"
    configuration.write_text(
        'CAREER_APP_NAME="Configured career assistant"\n'
        "OPENAI_API_KEY=synthetic-test-value\n"
    )

    settings = Settings(_env_file=configuration)

    assert settings.app_name == "Configured career assistant"
    assert settings.openai_api_key.get_secret_value() == "synthetic-test-value"
    assert "OPENAI_API_KEY" not in settings.model_dump()
    assert "synthetic-test-value" not in settings.model_dump_json()


def test_render_and_s3_environment_wire_private_persistence(tmp_path):
    configuration = tmp_path / ".env.local"
    configuration.write_text(
        "DATABASE_URL=postgresql://owner:secret@dpg-test-a/db\n"
        "DATABASE_URL_UNPOOLED=postgresql://owner:secret@dpg-test-a.frankfurt-postgres.render.com/db\n"
        "AWS_ENDPOINT_URL_S3=https://storage.example.invalid\n"
        "AWS_REGION=auto\n"
        "AWS_ACCESS_KEY_ID=synthetic-storage-key\n"
        "AWS_SECRET_ACCESS_KEY=synthetic-storage-secret\n"
        "CAREER_DOCUMENT_BACKEND=s3\n"
        "CAREER_S3_BUCKET=assets\n"
    )
    settings = Settings(_env_file=configuration)
    runtime = database_url(settings)
    migration = database_url(settings, direct=True)
    assert runtime.host == "dpg-test-a"
    assert migration.host == "dpg-test-a.frankfurt-postgres.render.com"
    assert runtime.query["sslmode"] == "require"
    assert migration.query["sslmode"] == "verify-full"
    assert migration.query["sslrootcert"] == "system"
    store = document_store(settings)
    assert isinstance(store, S3DocumentStore)
    assert store.bucket == "assets"
    assert store.client.meta.endpoint_url == "https://storage.example.invalid"
    assert store.client.meta.region_name == "auto"
    assert store.client.meta.config.s3["addressing_style"] == "path"
    assert "synthetic-storage-secret" not in settings.model_dump_json()


def test_local_env_overrides_base_env_without_losing_other_secrets(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "CAREER_APP_NAME=Base app\nOPENAI_API_KEY=preserved-key\n"
    )
    (tmp_path / ".env.local").write_text("CAREER_APP_NAME=Local app\n")
    settings = Settings()
    assert settings.app_name == "Local app"
    assert settings.openai_api_key.get_secret_value() == "preserved-key"
