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
