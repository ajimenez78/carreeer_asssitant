from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAREER_", env_file=".env", extra="ignore"
    )

    app_name: str = "Career assistant"
