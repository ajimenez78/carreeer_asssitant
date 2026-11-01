from career_assistant.config import Settings


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
