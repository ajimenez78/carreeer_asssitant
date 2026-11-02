"""Private release, backup, restore and Render startup commands. No public routes."""

import argparse
import json
import os
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit

import psycopg
from alembic.script import ScriptDirectory
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError
from sqlalchemy import inspect, make_url, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from career_assistant.backup import (
    BackupBucket,
    BackupError,
    create_archive,
    restore_archive,
    validate_archive,
)
from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    migrate_database,
    migration_config,
    render_private_database,
)
from career_assistant.models import Owner
from career_assistant.persistence import ensure_owner
from career_assistant.storage import LocalDocumentStore, document_store


def validate_production(settings):
    if (
        not settings.database_url
        or not settings.session_secret
        or len(settings.session_secret.get_secret_value()) < 32
    ):
        raise BackupError(
            "Configure the production database and stable session secret."
        )
    if not settings.session_secure or not settings.allowed_origins:
        raise BackupError("Production requires secure cookies and exact HTTPS origins.")
    for origin in settings.allowed_origins:
        url = urlsplit(origin)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.path
            or url.query
            or url.fragment
        ):
            raise BackupError("Use exact HTTPS origins without paths or credentials.")
    url = database_url(settings)
    if url.host in {None, "localhost", "127.0.0.1", "::1", "db"} or (
        url.query.get("sslmode") != "verify-full"
        and not (render_private_database(url) and url.query.get("sslmode") == "require")
    ):
        raise BackupError(
            "Production requires verified external TLS or encrypted Render private SQL."
        )
    if (
        not settings.openai_api_key
        or not settings.openai_api_key.get_secret_value().strip()
    ):
        raise BackupError("Configure the backend OpenAI key.")
    if settings.document_backend != "s3":
        raise BackupError(
            "Production originals must use private S3-compatible object storage."
        )
    document_store(settings)


def release(settings, *, backup_key=None):
    url = database_url(settings, direct=True)
    engine = database_engine(url)
    try:
        tables = inspect(engine).get_table_names()
        head = ScriptDirectory.from_config(migration_config()).get_current_head()
        if tables:
            if "alembic_version" not in tables:
                raise BackupError(
                    "Existing database is not migration-managed; "
                    "inspect it before release."
                )
            with engine.connect() as connection:
                current = connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
            if current != head:
                if not backup_key:
                    raise BackupError(
                        "Back up the existing database before migrating; "
                        "pass its completed backup key."
                    )
                BackupBucket(settings).verify_recent(backup_key, url, datetime.now(UTC))
        migrate_database(url)
        with sessionmaker(engine).begin() as session:
            ensure_owner(session)
    finally:
        engine.dispose()


def verify_ready(settings):
    engine = database_engine(database_url(settings))
    try:
        with engine.connect() as connection:
            if (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                != ScriptDirectory.from_config(migration_config()).get_current_head()
            ):
                raise BackupError(
                    "Run the separate release migration before starting this image."
                )
        with sessionmaker(engine)() as session:
            owner = session.scalar(select(Owner).where(Owner.id == 1))
            if owner is None or not owner.password_hash:
                raise BackupError(
                    "Configure the owner with the private owner command before startup."
                )
    finally:
        engine.dispose()


def run_backup(settings):
    started = monotonic()
    bucket = BackupBucket(settings)
    url = database_url(settings, direct=True)
    engine = database_engine(url)
    try:
        with tempfile.TemporaryDirectory(prefix="career-backup-") as directory:
            path = Path(directory) / "backup.zip"
            manifest = create_archive(
                sessionmaker(engine), url, document_store(settings), path
            )
            validate_archive(path)
            key = bucket.put(path, manifest)
            # Read back and verify all bytes before pruning older recovery points.
            verification = Path(directory) / "verified.zip"
            downloaded = bucket.download(key, verification)
            if downloaded != manifest:
                raise BackupError(
                    "Published manifest verification failed; old backups retained."
                )
            removed = bucket.prune(datetime.now(UTC))
            return {
                "event": "backup_completed",
                "key": key,
                "bytes": path.stat().st_size,
                "originals": len(manifest.originals),
                "expired_removed": removed,
                "elapsed_seconds": round(monotonic() - started, 3),
            }
    finally:
        engine.dispose()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve")
    commands.add_parser("preflight")
    migration = commands.add_parser("release")
    migration.add_argument("--backup-key")
    backup = commands.add_parser("backup")
    backup.add_argument(
        "--output", type=Path, help="Private local archive instead of uploading/pruning"
    )
    recovery = commands.add_parser("restore")
    recovery.add_argument("archive", type=Path)
    recovery.add_argument("--target-env", default="CAREER_RESTORE_DATABASE_URL")
    recovery.add_argument("--documents-directory", type=Path)
    recovery.add_argument("--allow-remote", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "restore":
            configured = os.environ.get(args.target_env)
            if not configured:
                raise BackupError("Set a separate restoration database variable.")
            target = make_url(configured).set(drivername="postgresql+psycopg")
            if target.host not in {"localhost", "127.0.0.1", "::1"}:
                if (
                    not args.allow_remote
                    or target.query.get("sslmode") != "verify-full"
                ):
                    raise BackupError(
                        "Remote recovery requires --allow-remote and verified TLS."
                    )
            store = (
                LocalDocumentStore(args.documents_directory)
                if args.documents_directory
                else document_store(
                    Settings(
                        _env_file=None,
                        _env_prefix="CAREER_RESTORE_",
                        document_backend="s3",
                        # Recovery must never inherit the live AWS_* aliases.
                        s3_endpoint=os.environ.get("CAREER_RESTORE_S3_ENDPOINT"),
                        s3_region=os.environ.get("CAREER_RESTORE_S3_REGION", "auto"),
                        s3_bucket=os.environ.get("CAREER_RESTORE_S3_BUCKET"),
                        s3_access_key=os.environ.get("CAREER_RESTORE_S3_ACCESS_KEY"),
                        s3_secret_key=os.environ.get("CAREER_RESTORE_S3_SECRET_KEY"),
                    )
                )
            )
            manifest = restore_archive(args.archive, target, store)
            result = {
                "event": "restored",
                "originals": len(manifest.originals),
                "revision": manifest.revision,
            }
        else:
            # Render injects this stable HTTPS URL before startup. Custom domains
            # can instead supply an explicit CAREER_ALLOWED_ORIGINS JSON array.
            if (
                args.command in {"serve", "preflight"}
                and not os.environ.get("CAREER_ALLOWED_ORIGINS")
                and os.environ.get("RENDER_EXTERNAL_URL")
            ):
                os.environ["CAREER_ALLOWED_ORIGINS"] = json.dumps(
                    [os.environ["RENDER_EXTERNAL_URL"]]
                )
            settings = Settings()
            if args.command in {"serve", "preflight"}:
                validate_production(settings)
                verify_ready(settings)
                if args.command == "serve":
                    import uvicorn

                    uvicorn.run(
                        "career_assistant.main:app",
                        host="0.0.0.0",
                        port=int(os.environ.get("PORT", "8000")),
                    )
                    return
                result = {"event": "production_preflight_passed"}
            elif args.command == "release":
                release(settings, backup_key=args.backup_key)
                result = {"event": "database_release_completed"}
            elif args.output:
                url = database_url(settings, direct=True)
                engine = database_engine(url)
                try:
                    manifest = create_archive(
                        sessionmaker(engine), url, document_store(settings), args.output
                    )
                    validate_archive(args.output)
                    result = {
                        "event": "private_backup_created",
                        "bytes": args.output.stat().st_size,
                        "originals": len(manifest.originals),
                    }
                finally:
                    engine.dispose()
            else:
                result = run_backup(settings)
        print(json.dumps(result))
    except BackupError as error:
        parser.exit(1, f"Operation failed: {error}\n")
    except (
        OSError,
        ValueError,
        KeyError,
        ValidationError,
        psycopg.Error,
        SQLAlchemyError,
        BotoCoreError,
        ClientError,
        zipfile.BadZipFile,
    ):
        parser.exit(
            1,
            "Operation failed. Check private database/storage settings and tool "
            "availability; no credentials or source content are logged.\n",
        )


if __name__ == "__main__":
    main()
