"""Explicit local initialization, hosted migration, and retryable file cleanup."""

import argparse

import psycopg
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    ensure_local_database,
    migrate_database,
)
from career_assistant.persistence import ensure_owner
from career_assistant.storage import cleanup_documents, document_store


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "migrate", "cleanup"])
    args = parser.parse_args(argv)
    try:
        settings = Settings()
        url = database_url(settings, direct=args.command != "cleanup")
        if args.command == "init":
            ensure_local_database(url)
        if args.command != "cleanup":
            migrate_database(url)
        engine = database_engine(url)
        try:
            sessions = sessionmaker(engine, expire_on_commit=False)
            if args.command == "cleanup":
                count = cleanup_documents(sessions, document_store(settings))
                print(f"Removed {count} queued original documents.")
            else:
                with sessions.begin() as session:
                    ensure_owner(session)
                print(
                    "Database is at the latest migration; configured owner preserved."
                )
        finally:
            engine.dispose()
    except (
        BotoCoreError,
        ClientError,
        ValidationError,
        ValueError,
        psycopg.Error,
        SQLAlchemyError,
        OSError,
    ) as error:
        # Driver messages can contain connection parameters or SQL/source contents.
        parser.exit(
            1,
            f"Database command failed ({type(error).__name__}). "
            "Check backend configuration and PostgreSQL/storage availability.\n",
        )


if __name__ == "__main__":
    main()
