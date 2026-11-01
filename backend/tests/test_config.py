from career_assistant.config import Settings


def test_settings_ignore_unrelated_provider_secrets(tmp_path):
    configuration = tmp_path / ".env"
    configuration.write_text(
        'CAREER_APP_NAME="Configured career assistant"\n'
        "OPENAI_API_KEY=synthetic-test-value\n"
    )

    settings = Settings(_env_file=configuration)

    assert settings.app_name == "Configured career assistant"
    assert settings.model_dump() == {"app_name": "Configured career assistant"}
