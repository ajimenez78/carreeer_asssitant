from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAREER_", env_file=".env", extra="ignore", populate_by_name=True
    )

    app_name: str = "Career assistant"
    database_url: SecretStr | None = Field(
        default=None, validation_alias="DATABASE_URL"
    )
    database_direct_url: SecretStr | None = Field(
        default=None, validation_alias="DATABASE_DIRECT_URL"
    )
    postgres_password: SecretStr = SecretStr("local-development-only")
    postgres_host: str = "127.0.0.1"
    document_backend: Literal["local", "neon"] = "local"
    document_directory: Path = Path(".data/documents")
    neon_storage_endpoint: str | None = None
    neon_storage_region: str = "eu-central-1"
    neon_storage_bucket: str | None = None
    neon_storage_access_key: SecretStr | None = None
    neon_storage_secret_key: SecretStr | None = None
    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )
    ai_model: str = Field(default="gpt-6-luna", min_length=1)
    ai_reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"] = (
        "low"
    )
    ai_timeout_seconds: float = Field(default=60, gt=0, le=60)
    ai_max_input_tokens: int = Field(default=20_000, ge=1, le=20_000)
    ai_max_output_tokens: int = Field(default=2_000, ge=1, le=2_000)
