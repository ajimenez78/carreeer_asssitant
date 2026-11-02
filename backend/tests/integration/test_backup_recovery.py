"""Real PostgreSQL exports/restores; only disposable synthetic databases and files."""

import json
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import inspect, text

from career_assistant.auth import PASSWORDS
from career_assistant.backup import (
    BackupError,
    PostgresTools,
    create_archive,
    restore_archive,
    validate_archive,
)
from career_assistant.config import Settings
from career_assistant.database import database_engine, ensure_local_database
from career_assistant.models import Owner, OwnerSession
from career_assistant.operations import release, verify_ready
from career_assistant.persistence import (
    DefinitionData,
    DefinitionRepository,
    PreferenceData,
    SourceData,
)
from career_assistant.storage import LocalDocumentStore, cleanup_documents


def tools():
    if image := os.environ.get("CAREER_BACKUP_TOOLS_IMAGE"):
        return PostgresTools(
            (
                "docker",
                "run",
                "--rm",
                "-i",
                "--network",
                "container:career-assistant-local-db-1",
                "-e",
                "PGHOST",
                "-e",
                "PGPORT",
                "-e",
                "PGUSER",
                "-e",
                "PGPASSWORD",
                "-e",
                "PGDATABASE",
                image,
            )
        )
    return PostgresTools(
        (
            "docker",
            "compose",
            "exec",
            "-T",
            "-e",
            "PGHOST",
            "-e",
            "PGPORT",
            "-e",
            "PGUSER",
            "-e",
            "PGPASSWORD",
            "-e",
            "PGDATABASE",
            "db",
        )
    )


def populate(sessions, tmp_path):
    store = LocalDocumentStore(tmp_path / "originals")
    content = b"# Synthetic background\nPreviously developed software."
    with sessions.begin() as session:
        owner = session.get(Owner, 1)
        owner.password_hash = PASSWORDS.hash("synthetic-recovery-password")
        session.add(
            OwnerSession(owner_id=1, expires_at=datetime.now(UTC) + timedelta(hours=1))
        )
        repo = DefinitionRepository(session)
        repo.save(
            DefinitionData(
                description="Staff engineer, remote in Spain",
                preferences=[
                    PreferenceData(key="salary", category="compensation", value=None)
                ],
            )
        )
        source = repo.add_source(
            SourceData(
                kind="file",
                display_name="synthetic.md",
                object_key=uuid4(),
                media_type="text/markdown",
                size_bytes=len(content),
            )
        )
        source.original_stored = True
        store.put(source.object_key, content)
        repo.record_extraction(source.id, text=content.decode())
        repo.review_source(source.id, ["Previously developed software."])
        question = repo.add_clarifications(["What compensation do you prefer?"])[0]
        repo.answer_clarification(question.id, "unknown")
        repo.add_chat_turn(
            identity=uuid4(),
            message="Discuss work-life balance",
            language="English",
            response={
                "in_scope": True,
                "reply": "What hours suit you?",
                "proposal": {"preferences": [], "conflicts": []},
                "questions": [],
            },
        )
        repo.set_clarification_paused(True)
        return store, source.id, source.object_key, content


def rows(engine):
    with engine.connect() as connection:
        return {
            name: sorted(
                json.dumps(dict(row), default=str, sort_keys=True)
                for row in connection.execute(
                    text(f'SELECT * FROM "{name}"')
                ).mappings()
            )
            for name in inspect(engine).get_table_names()
        }


@pytest.fixture
def replacement(database):
    url = database.url.set(database="career_restore_" + uuid4().hex)
    ensure_local_database(url)
    engine = database_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()
        with psycopg.connect(
            url.set(drivername="postgresql", database="postgres").render_as_string(
                hide_password=False
            ),
            autocommit=True,
        ) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    sql.Identifier(url.database)
                )
            )


def test_snapshot_export_and_restore_preserve_all_data_and_originals(
    sessions, database, replacement, tmp_path
):
    store, _, key, content = populate(sessions, tmp_path)
    before = rows(database)
    archive = tmp_path / "backup.zip"
    manifest = create_archive(sessions, database.url, store, archive, tools=tools())
    assert archive.stat().st_mode & 0o777 == 0o600
    assert manifest.revision == "0005" and len(manifest.originals) == 1
    assert validate_archive(archive) == manifest
    restored_store = LocalDocumentStore(tmp_path / "restored")
    restore_archive(archive, replacement.url, restored_store, tools=tools())
    assert restored_store.get(key) == content
    assert rows(replacement) == before
    assert rows(database) == before
    with pytest.raises(BackupError, match="empty replacement"):
        restore_archive(archive, replacement.url, restored_store, tools=tools())


def test_backup_freezes_source_deletion_until_originals_are_captured(
    sessions, database, tmp_path
):
    store, source_id, key, content = populate(sessions, tmp_path)
    started, completed = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as executor:
        tasks = []

        def remove():
            started.set()
            with sessions.begin() as session:
                DefinitionRepository(session).delete_source(source_id)
            cleanup_documents(sessions, store)
            completed.set()

        class Dump:
            def dump(self, url, snapshot, stream):
                tasks.append(executor.submit(remove))
                assert started.wait(2)
                assert not completed.wait(0.1)
                stream.write(b"synthetic SQL snapshot")

        path = tmp_path / "locked.zip"
        create_archive(sessions, database.url, store, path, tools=Dump())
        tasks[0].result(timeout=5)
    assert completed.is_set()
    with pytest.raises(FileNotFoundError):
        store.get(key)
    with zipfile.ZipFile(path) as archive:
        assert archive.read(f"documents/{key}") == content


def test_missing_original_does_not_publish_an_incomplete_archive(
    sessions, database, tmp_path
):
    store, _, key, _ = populate(sessions, tmp_path)
    store.delete(key)
    path = tmp_path / "incomplete.zip"

    class Dump:
        def dump(self, url, snapshot, stream):
            stream.write(b"synthetic SQL")

    with pytest.raises(FileNotFoundError):
        create_archive(sessions, database.url, store, path, tools=Dump())
    assert not path.exists()


def test_release_preserves_owner_and_requires_readiness(sessions, database):
    settings = Settings(
        _env_file=None, database_url=database.url.render_as_string(hide_password=False)
    )
    with pytest.raises(BackupError, match="owner"):
        verify_ready(settings)
    with sessions.begin() as session:
        session.get(Owner, 1).password_hash = PASSWORDS.hash(
            "synthetic-recovery-password"
        )
    before = rows(database)
    release(settings)
    release(settings)
    verify_ready(settings)
    assert rows(database) == before


def test_restore_failure_removes_new_originals_and_keeps_database_empty(
    sessions, database, replacement, tmp_path
):
    store, _, key, _ = populate(sessions, tmp_path)
    path = tmp_path / "restore-failure.zip"

    class FakeDump:
        def dump(self, url, snapshot, output):
            output.write(b"synthetic dump")

    class FailedRestore:
        def restore(self, url, stream):
            raise BackupError("Synthetic restoration failure")

    create_archive(sessions, database.url, store, path, tools=FakeDump())
    destination = LocalDocumentStore(tmp_path / "destination")
    with pytest.raises(BackupError):
        restore_archive(path, replacement.url, destination, tools=FailedRestore())
    assert inspect(replacement).get_table_names() == []
    with pytest.raises(FileNotFoundError):
        destination.get(key)


def test_schema_change_requires_a_verified_backup_before_migration(
    replacement, monkeypatch
):
    from career_assistant import operations
    from career_assistant.database import migrate_database

    migrate_database(replacement.url, revision="0004")
    settings = Settings(
        _env_file=None,
        database_url=replacement.url.render_as_string(hide_password=False),
    )
    with pytest.raises(BackupError, match="Back up"):
        release(settings)
    with replacement.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == "0004"
        )
    verified = []

    class Bucket:
        def verify_recent(self, key, url, now):
            verified.append(key)

    monkeypatch.setattr(operations, "BackupBucket", lambda settings: Bucket())
    release(settings, backup_key="completed-backup.zip")
    assert verified == ["completed-backup.zip"]
    with replacement.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005"
        )
