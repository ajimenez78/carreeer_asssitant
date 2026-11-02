"""Consistent SQL/original backups and recovery into empty replacement resources."""

import base64
import hashlib
import os
import re
import subprocess
import tempfile
import threading
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import boto3
import psycopg
from botocore.config import Config
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import URL, select, text

from career_assistant.config import Settings
from career_assistant.models import DocumentDeletion, JobDefinition, Owner, Source

MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
CHUNK = 1024 * 1024
BACKUP_NAME = re.compile(r"\d{8}T\d{6}Z-[a-f0-9]{32}\.zip$")


class BackupError(Exception):
    """Only fixed diagnostic messages may be shown to operators."""


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    size: int = Field(ge=0, le=MAX_ARCHIVE_BYTES)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format: int = Field(default=1, ge=1, le=1)
    created_at: datetime
    database_identity: str = Field(pattern="^[a-f0-9]{64}$")
    revision: str
    database: Entry
    originals: list[Entry] = Field(max_length=5)


def database_identity(url: URL) -> str:
    return hashlib.sha256(
        f"{url.host}:{url.port or 5432}/{url.database}".encode()
    ).hexdigest()


def pg_environment(url: URL) -> dict:
    # Credentials are environment-only, never process arguments or diagnostics.
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("PG"):
            env.pop(key)
    env.update(
        PGHOST=url.host or "",
        PGPORT=str(url.port or 5432),
        PGUSER=url.username or "",
        PGPASSWORD=url.password or "",
        PGDATABASE=url.database or "",
        PGCONNECT_TIMEOUT="10",
    )
    for key in ("sslmode", "sslrootcert", "channel_binding"):
        if key in url.query:
            env["PG" + key.upper().replace("_", "")] = url.query[key]
    return env


class PostgresTools:
    def __init__(self, prefix=()):
        self.prefix = tuple(prefix)

    def dump(self, url, snapshot, output):
        with subprocess.Popen(
            [
                *self.prefix,
                "pg_dump",
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--no-tablespaces",
                f"--snapshot={snapshot}",
            ],
            env=pg_environment(url),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ) as process:
            timer = threading.Timer(240, process.kill)
            timer.start()
            try:
                copy_bounded(process.stdout, output)
                if process.wait(timeout=10):
                    raise BackupError(
                        "PostgreSQL export failed; no backup was published."
                    )
            finally:
                timer.cancel()
                if process.poll() is None:
                    process.kill()

    def restore(self, url, stream):
        with subprocess.Popen(
            [
                *self.prefix,
                "pg_restore",
                "--dbname",
                url.database,
                "--single-transaction",
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "--no-tablespaces",
            ],
            env=pg_environment(url),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) as process:
            timer = threading.Timer(240, process.kill)
            timer.start()
            try:
                copy_bounded(stream, process.stdin)
                process.stdin.close()
                if process.wait(timeout=10):
                    raise BackupError(
                        "PostgreSQL recovery failed; target is not ready."
                    )
            finally:
                timer.cancel()
                if process.poll() is None:
                    process.kill()


def copy_bounded(source, target, limit=MAX_ARCHIVE_BYTES) -> tuple[int, str]:
    digest, size = hashlib.sha256(), 0
    while chunk := source.read(CHUNK):
        size += len(chunk)
        if size > limit:
            raise BackupError("Backup content exceeds the supported size limit.")
        digest.update(chunk)
        if target is not None:
            target.write(chunk)
    return size, digest.hexdigest()


def create_archive(sessions, url, originals, output: Path, *, tools=None, now=None):
    tools = tools or PostgresTools()
    now = now or datetime.now(UTC)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Exclusive creation prevents overwriting another backup or following a symlink.
    try:
        with output.open("xb") as raw:
            output.chmod(0o600)
            with sessions.begin() as session:
                session.execute(text("SET LOCAL lock_timeout = '10s'"))
                session.execute(
                    text("SET LOCAL idle_in_transaction_session_timeout = '300s'")
                )
                # The same order as save: prevent new definitions, mutations and
                # original writes. Cleanup skips the queued originals locked here.
                list(session.scalars(select(Owner).with_for_update()))
                list(session.scalars(select(JobDefinition).with_for_update()))
                list(session.scalars(select(DocumentDeletion).with_for_update()))
                snapshot = session.scalar(text("SELECT pg_export_snapshot()"))
                revision = session.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
                rows = list(
                    session.scalars(select(Source).where(Source.original_stored))
                )
                if len(rows) > 5:
                    raise BackupError(
                        "Original metadata exceeds the supported file limit."
                    )
                with zipfile.ZipFile(
                    raw, "w", compression=zipfile.ZIP_STORED
                ) as archive:
                    with archive.open("database.dump", "w", force_zip64=True) as stream:
                        tools.dump(url, snapshot, stream)
                    entries = []
                    for source in rows:
                        content = originals.get(source.object_key)
                        if (
                            len(content) != source.size_bytes
                            or len(content) > 10 * 1024 * 1024
                        ):
                            raise BackupError(
                                "An original is missing or has inconsistent size."
                            )
                        name = f"documents/{source.object_key}"
                        archive.writestr(name, content)
                        entries.append(
                            Entry(
                                name=name,
                                size=len(content),
                                sha256=hashlib.sha256(content).hexdigest(),
                            )
                        )
                    # Read the written dump through a second ZIP reader only after
                    # the archive is finalized below; its checksum is filled later.
                if raw.tell() > MAX_ARCHIVE_BYTES:
                    raise BackupError(
                        "Backup archive exceeds 512 MiB; reduce stored data."
                    )
            # Locks can be released once SQL and every required original are captured.
        with zipfile.ZipFile(output) as archive:
            with archive.open("database.dump") as stream:
                size, digest = copy_bounded(stream, None)
        manifest = Manifest(
            created_at=now,
            database_identity=database_identity(url),
            revision=revision,
            database=Entry(name="database.dump", size=size, sha256=digest),
            originals=entries,
        )
        with zipfile.ZipFile(output, "a") as archive:
            archive.writestr("manifest.json", manifest.model_dump_json())
        if output.stat().st_size > MAX_ARCHIVE_BYTES:
            raise BackupError("Backup archive exceeds 512 MiB; reduce stored data.")
        return manifest
    except FileExistsError:
        raise BackupError(
            "Choose a new backup path; the output already exists."
        ) from None
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def validate_archive(path: Path) -> Manifest:
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise BackupError("Backup archive exceeds 512 MiB.")
    with zipfile.ZipFile(path) as archive:
        if archive.getinfo("manifest.json").file_size > 64 * 1024:
            raise BackupError("Backup manifest is too large.")
        manifest = Manifest.model_validate_json(archive.read("manifest.json"))
        expected = ["manifest.json", "database.dump"]
        if manifest.database.name != "database.dump":
            raise BackupError("Invalid database entry.")
        for entry in manifest.originals:
            if (
                entry.name != f"documents/{UUID(entry.name.removeprefix('documents/'))}"
                or entry.size > 10 * 1024 * 1024
            ):
                raise BackupError("Invalid original entry.")
            expected.append(entry.name)
        if len(set(expected)) != len(expected) or sorted(archive.namelist()) != sorted(
            expected
        ):
            raise BackupError("Archive entries do not match the manifest.")
        for entry in [manifest.database, *manifest.originals]:
            if archive.getinfo(entry.name).file_size != entry.size:
                raise BackupError("Backup entry has an inconsistent size.")
            with archive.open(entry.name) as stream:
                size, digest = copy_bounded(stream, None, entry.size)
            if size != entry.size or digest != entry.sha256:
                raise BackupError("Backup integrity verification failed.")
        return manifest


def restore_archive(path, target_url, originals, *, tools=None):
    manifest = validate_archive(path)
    with psycopg.connect(
        target_url.set(drivername="postgresql").render_as_string(hide_password=False),
        connect_timeout=10,
    ) as connection:
        if connection.execute(
            "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN "
            "('pg_catalog', 'information_schema')"
        ).fetchone()[0]:
            raise BackupError("Restore requires an empty replacement database.")
    # Refuse overwriting any original, even with an empty database.
    for entry in manifest.originals:
        try:
            originals.get(UUID(entry.name.split("/")[1]))
        except FileNotFoundError:
            pass
        else:
            raise BackupError("Restore target already contains a matching original.")
    uploaded = []
    try:
        with zipfile.ZipFile(path) as archive:
            for entry in manifest.originals:
                key = UUID(entry.name.split("/")[1])
                uploaded.append(key)
                originals.put(key, archive.read(entry.name))
            with archive.open("database.dump") as stream:
                (tools or PostgresTools()).restore(target_url, stream)
    except BaseException:
        for key in uploaded:
            originals.delete(key)
        raise
    return manifest


class BackupBucket:
    def __init__(self, settings: Settings):
        from urllib.parse import urlsplit

        if not all(
            (
                settings.backup_endpoint,
                settings.backup_bucket,
                settings.backup_access_key,
                settings.backup_secret_key,
            )
        ):
            raise BackupError("Configure the independent private backup bucket.")
        endpoint = urlsplit(settings.backup_endpoint)
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username:
            raise BackupError(
                "Backup storage requires a credential-free HTTPS endpoint."
            )
        if not re.fullmatch(r"[a-zA-Z0-9_-]+/", settings.backup_prefix):
            raise BackupError("Use one dedicated backup prefix ending with '/'.")
        self.bucket, self.prefix = settings.backup_bucket, settings.backup_prefix
        if (
            settings.s3_endpoint == settings.backup_endpoint
            and settings.s3_bucket == settings.backup_bucket
        ):
            raise BackupError(
                "Backups must use a separate private bucket from originals."
            )
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.backup_endpoint,
            region_name=settings.backup_region,
            aws_access_key_id=settings.backup_access_key.get_secret_value(),
            aws_secret_access_key=settings.backup_secret_key.get_secret_value(),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                connect_timeout=10,
                read_timeout=60,
                retries={"max_attempts": 2},
                request_checksum_calculation="when_required",
            ),
        )

    def put(self, path, manifest):
        key = (
            self.prefix
            + manifest.created_at.strftime("%Y%m%dT%H%M%SZ")
            + f"-{uuid4().hex}.zip"
        )
        with path.open("rb") as stream:
            checksum = base64.b64encode(
                hashlib.file_digest(stream, "md5").digest()
            ).decode()
            stream.seek(0)
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=stream,
                ContentMD5=checksum,
                ContentType="application/zip",
                Metadata={
                    "database-identity": manifest.database_identity,
                    "created-at": manifest.created_at.isoformat(),
                },
            )
        response = self.client.head_object(Bucket=self.bucket, Key=key)
        if response["ContentLength"] != path.stat().st_size:
            raise BackupError(
                "Uploaded backup size verification failed; retention was not pruned."
            )
        return key

    def download(self, key, path):
        if not key.startswith(self.prefix) or not BACKUP_NAME.fullmatch(
            key.removeprefix(self.prefix)
        ):
            raise BackupError("Select a backup key from the dedicated prefix.")
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        if response["ContentLength"] > MAX_ARCHIVE_BYTES:
            response["Body"].close()
            raise BackupError("Backup archive exceeds 512 MiB.")
        with response["Body"] as stream, path.open("xb") as output:
            path.chmod(0o600)
            copy_bounded(stream, output)
        return validate_archive(path)

    def prune(self, now):
        removed = 0
        for page in self.client.get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket, Prefix=self.prefix
        ):
            for row in page.get("Contents", []):
                if BACKUP_NAME.fullmatch(row["Key"].removeprefix(self.prefix)) and row[
                    "LastModified"
                ] <= now - timedelta(days=7):
                    self.client.delete_object(Bucket=self.bucket, Key=row["Key"])
                    removed += 1
        return removed

    def verify_recent(self, key, url, now):
        if not key.startswith(self.prefix) or not BACKUP_NAME.fullmatch(
            key.removeprefix(self.prefix)
        ):
            raise BackupError(
                "Select a completed backup key from the dedicated prefix."
            )
        row = self.client.head_object(Bucket=self.bucket, Key=key)
        created = datetime.fromisoformat(row["Metadata"]["created-at"])
        if created.tzinfo is None:
            raise BackupError("Backup metadata has no UTC offset.")
        if row["Metadata"].get("database-identity") != database_identity(
            url
        ) or not timedelta(0) <= now - created <= timedelta(days=1):
            raise BackupError(
                "Migration requires a backup of this database from the last 24 hours."
            )

        with tempfile.TemporaryDirectory(prefix="career-verify-") as directory:
            manifest = self.download(key, Path(directory) / "backup.zip")
            if (
                manifest.database_identity != database_identity(url)
                or manifest.created_at != created
            ):
                raise BackupError(
                    "Backup manifest does not match the selected database."
                )
