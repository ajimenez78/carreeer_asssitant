import pytest
from pydantic import SecretStr
from sqlalchemy import URL

from career_assistant.config import Settings
from career_assistant.database import database_url, require_local_database
from career_assistant.db_cli import main


def test_database_urls_keep_secrets_and_prefer_direct_for_migrations():
    settings = Settings(
        _env_file=None,
        database_url=SecretStr(
            "postgres://user:runtime-secret@runtime.invalid/db?sslmode=require"
        ),
        database_direct_url=SecretStr(
            "postgresql://user:direct-secret@direct.invalid/db?sslmode=require"
        ),
    )
    assert database_url(settings).host == "runtime.invalid"
    direct = database_url(settings, direct=True)
    assert direct.drivername == "postgresql+psycopg"
    assert direct.host == "direct.invalid"
    assert direct.query["sslmode"] == "require"
    assert "direct-secret" not in repr(direct)
    assert "runtime-secret" not in settings.model_dump_json()
    assert "direct-secret" not in repr(settings)


def test_local_url_escapes_password_without_changing_it():
    settings = Settings(_env_file=None, postgres_password="synthetic@:/%password")
    assert database_url(settings).password == "synthetic@:/%password"
    assert database_url(settings, direct=True) == database_url(settings)


@pytest.mark.parametrize("host", ["remote.invalid", None])
def test_database_creation_refuses_remote_or_implicit_connections(host):
    with pytest.raises(ValueError, match="restricted to local"):
        require_local_database(
            URL.create("postgresql+psycopg", host=host, database="db")
        )


def test_non_postgres_url_is_rejected():
    with pytest.raises(ValueError, match="PostgreSQL"):
        database_url(Settings(_env_file=None, database_url="sqlite:///local.db"))


def test_cli_diagnostics_do_not_print_connection_secrets(monkeypatch, capsys):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:synthetic-secret@remote.invalid/db"
    )
    monkeypatch.delenv("DATABASE_DIRECT_URL", raising=False)
    with pytest.raises(SystemExit) as error:
        main(["init"])
    assert error.value.code == 1
    diagnostics = capsys.readouterr().err
    assert "Database command failed" in diagnostics
    assert "synthetic-secret" not in diagnostics
    assert "remote.invalid" not in diagnostics
