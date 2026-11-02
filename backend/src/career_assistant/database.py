"""Connection and explicit migration helpers; importing this opens no connections."""

import re
import ssl
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import URL, Engine, create_engine, make_url
from sqlalchemy.pool import NullPool

from career_assistant.config import Settings


def database_url(settings: Settings, *, direct: bool = False) -> URL:
    configured = (
        settings.database_direct_url if direct else None
    ) or settings.database_url
    url = (
        make_url(configured.get_secret_value())
        if configured
        else URL.create(
            "postgresql+psycopg",
            username="career",
            password=settings.postgres_password.get_secret_value(),
            host=settings.postgres_host,
            port=5432,
            database="career",
        )
    )
    if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise ValueError("A PostgreSQL URL is required")
    if render_private_database(url):
        # Render's internal certificates are self-signed. Require encryption.
        if "sslmode" not in url.query:
            url = url.update_query_dict({"sslmode": "require"})
    elif url.host and url.host.endswith("-postgres.render.com"):
        root = url.query.get("sslrootcert", "system")
        if root == "system":
            # Binary Psycopg's libpq can have different OpenSSL trust paths.
            root = ssl.get_default_verify_paths().cafile
            if root is None and Path("/etc/ssl/certs/ca-certificates.crt").is_file():
                root = "/etc/ssl/certs/ca-certificates.crt"
        url = url.update_query_dict(
            {"sslmode": "verify-full", "sslrootcert": root or "system"}
        )
    return url.set(drivername="postgresql+psycopg")


def render_private_database(url: URL) -> bool:
    return bool(re.fullmatch(r"dpg-[a-z0-9-]+", url.host or ""))


def database_engine(url: URL) -> Engine:
    return create_engine(
        url,
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 5, "prepare_threshold": None},
    )


def require_local_database(url: URL) -> None:
    if url.host not in {"localhost", "127.0.0.1", "::1"} or not url.database:
        raise ValueError("Database creation is restricted to local PostgreSQL")


def ensure_local_database(url: URL) -> bool:
    """Create only the requested local database; return whether it was created."""
    require_local_database(url)
    maintenance_url = url.set(drivername="postgresql", database="postgres")
    with psycopg.connect(
        maintenance_url.render_as_string(hide_password=False),
        autocommit=True,
        connect_timeout=5,
    ) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (url.database,)
        ).fetchone()
        if exists:
            return False
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database))
        )
    return True


def migration_config() -> Config:
    # Migrations are packaged with the backend for the separate release command.
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    return config


def migrate_database(url: URL, revision: str = "head") -> None:
    engine = database_engine(url)
    try:
        with engine.begin() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
    finally:
        engine.dispose()
