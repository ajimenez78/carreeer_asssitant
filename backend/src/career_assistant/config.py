from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAREER_",
        env_file=(".env", ".env.local"),
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Career assistant"
    frontend_directory: Path = Path("frontend/out")
    session_secret: SecretStr | None = None
    session_secure: bool = False
    allowed_origins: list[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]
    database_url: SecretStr | None = Field(
        default=None, validation_alias="DATABASE_URL"
    )
    database_direct_url: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_DIRECT_URL", "DATABASE_URL_UNPOOLED"),
    )
    postgres_password: SecretStr = SecretStr("local-development-only")
    postgres_host: str = "127.0.0.1"
    document_backend: Literal["local", "s3"] = "local"
    document_directory: Path = Path(".data/documents")
    s3_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CAREER_S3_ENDPOINT", "AWS_ENDPOINT_URL_S3"),
    )
    s3_region: str = Field(
        default="auto",
        validation_alias=AliasChoices("CAREER_S3_REGION", "AWS_REGION"),
    )
    s3_bucket: str | None = None
    s3_access_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("CAREER_S3_ACCESS_KEY", "AWS_ACCESS_KEY_ID"),
    )
    s3_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("CAREER_S3_SECRET_KEY", "AWS_SECRET_ACCESS_KEY"),
    )
    backup_endpoint: str | None = None
    backup_region: str = "auto"
    backup_bucket: str | None = None
    backup_access_key: SecretStr | None = None
    backup_secret_key: SecretStr | None = None
    backup_prefix: str = "career-backups/"
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
