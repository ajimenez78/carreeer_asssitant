"""Explicit local initialization, hosted migration, and retryable file cleanup."""

import argparse
import getpass

import psycopg
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from career_assistant.auth import PASSWORDS
from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    ensure_local_database,
    migrate_database,
)
from career_assistant.models import Owner, OwnerSession
from career_assistant.persistence import ensure_owner
from career_assistant.storage import cleanup_documents, document_store


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "migrate", "cleanup", "owner"])
    parser.add_argument("--username", default="owner")
    args = parser.parse_args(argv)
    try:
        settings = Settings()
        url = database_url(settings, direct=args.command in {"init", "migrate"})
        if args.command == "init":
            ensure_local_database(url)
        if args.command in {"init", "migrate"}:
            migrate_database(url)
        engine = database_engine(url)
        try:
            sessions = sessionmaker(engine, expire_on_commit=False)
            if args.command == "cleanup":
                count = cleanup_documents(sessions, document_store(settings))
                print(f"Removed {count} queued original documents.")
            elif args.command == "owner":
                password = getpass.getpass("Owner password (at least 12 characters): ")
                confirmation = getpass.getpass("Confirm password: ")
                if (
                    len(password) < 12
                    or len(password) > 1024
                    or password != confirmation
                    or not args.username.strip()
                    or len(args.username) > 100
                ):
                    raise ValueError("Invalid owner credentials")
                with sessions.begin() as session:
                    ensure_owner(session)
                    owner = session.get(Owner, 1)
                    owner.username = args.username.strip()
                    owner.password_hash = PASSWORDS.hash(password)
                    owner.failed_logins = 0
                    owner.locked_until = None
                    session.execute(delete(OwnerSession))
                print("Owner configured; previous sessions revoked.")
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
