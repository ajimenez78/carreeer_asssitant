import hashlib
import io
import zipfile
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

from career_assistant.backup import (
    BackupBucket,
    BackupError,
    Entry,
    Manifest,
    copy_bounded,
    create_archive,
    database_identity,
    pg_environment,
    validate_archive,
)
from career_assistant.config import Settings
from career_assistant.database import database_url
from career_assistant.operations import main, validate_production


def settings(**overrides):
    values = dict(
        _env_file=None,
        backup_endpoint="https://backup.invalid",
        backup_bucket="private-backups",
        backup_access_key="synthetic-key",
        backup_secret_key="synthetic-secret",
    )
    values.update(overrides)
    return Settings(**values)


def archive(path, *, damage=False, extra=None):
    original = f"documents/{uuid4()}"
    data = {"database.dump": b"synthetic SQL dump", original: b"synthetic original"}

    def entry(name, value):
        return Entry(
            name=name, size=len(value), sha256=hashlib.sha256(value).hexdigest()
        )

    manifest = Manifest(
        created_at=datetime.now(UTC),
        database_identity="a" * 64,
        revision="0005",
        database=entry("database.dump", data["database.dump"]),
        originals=[entry(original, data[original])],
    )
    with zipfile.ZipFile(path, "w") as output:
        for name, value in data.items():
            output.writestr(
                name, b"incorrect original" if damage and name == original else value
            )
        output.writestr("manifest.json", manifest.model_dump_json())
        if extra:
            output.writestr(extra, b"unexpected")
    return manifest


def test_archive_validates_all_bytes_and_rejects_extra_paths_or_corruption(tmp_path):
    valid = tmp_path / "valid.zip"
    expected = archive(valid)
    assert validate_archive(valid) == expected
    for case in ("corrupt", "extra", "traversal"):
        path = tmp_path / (case + ".zip")
        archive(
            path,
            damage=case == "corrupt",
            extra={"extra": "extra", "traversal": "../private"}.get(case),
        )
        with pytest.raises(BackupError):
            validate_archive(path)


def test_streaming_limit_and_output_exclusivity_preserve_existing_backups(tmp_path):
    with pytest.raises(BackupError):
        copy_bounded(io.BytesIO(b"x" * 11), io.BytesIO(), 10)
    existing = tmp_path / "saved.zip"
    existing.write_bytes(b"retained")
    with pytest.raises(BackupError, match="already exists"):
        create_archive(None, None, None, existing)
    assert existing.read_bytes() == b"retained"


def test_postgres_environment_keeps_passwords_out_of_process_arguments(monkeypatch):
    monkeypatch.setenv("PGSERVICE", "unexpected-service")
    url = database_url(
        Settings(
            _env_file=None,
            database_url="postgresql://owner:secret@db.invalid/db?sslmode=verify-full&sslrootcert=system&channel_binding=require",
        )
    )
    env = pg_environment(url)
    assert env["PGPASSWORD"] == "secret" and "PGSERVICE" not in env
    assert env["PGSSLMODE"] == "verify-full"
    assert env["PGSSLROOTCERT"] == "system" and env["PGCHANNELBINDING"] == "require"
    assert "secret" not in database_identity(url)


@pytest.mark.parametrize(
    "overrides",
    [
        {"backup_endpoint": "http://backup.invalid"},
        {"backup_endpoint": "https://name:secret@backup.invalid"},
        {"backup_access_key": None},
        {"backup_prefix": "../"},
        {"s3_endpoint": "https://backup.invalid", "s3_bucket": "private-backups"},
    ],
)
def test_backup_bucket_requires_independent_https_configuration(overrides):
    with pytest.raises(BackupError):
        BackupBucket(settings(**overrides))


def test_live_and_backup_buckets_can_use_separate_buckets_in_one_r2_account():
    bucket = BackupBucket(
        settings(s3_endpoint="https://backup.invalid", s3_bucket="private-originals")
    )
    assert bucket.bucket == "private-backups"


def test_production_accepts_render_private_tls_without_relaxing_public_tls():
    validate_production(
        production(database_url="postgresql://owner:secret@dpg-test-a/db")
    )
    with pytest.raises(BackupError):
        validate_production(
            production(
                database_url="postgresql://owner:secret@dpg-test-a/db?sslmode=disable"
            )
        )


def test_seven_day_retention_only_prunes_completed_backup_names():
    bucket = BackupBucket(settings())
    now = datetime.now(UTC)
    expired = bucket.prefix + "20261001T030000Z-" + "a" * 32 + ".zip"
    boundary = bucket.prefix + "20261002T030000Z-" + "b" * 32 + ".zip"
    recent = bucket.prefix + "20261102T030000Z-" + "c" * 32 + ".zip"
    other = bucket.prefix + "operator-notes.txt"
    with Stubber(bucket.client) as stub:
        stub.add_response(
            "list_objects_v2",
            {
                "Contents": [
                    {"Key": expired, "LastModified": now - timedelta(days=8)},
                    {"Key": boundary, "LastModified": now - timedelta(days=7)},
                    {"Key": recent, "LastModified": now},
                    {"Key": other, "LastModified": now - timedelta(days=30)},
                ]
            },
            {"Bucket": bucket.bucket, "Prefix": bucket.prefix},
        )
        for key in (expired, boundary):
            stub.add_response(
                "delete_object", {}, {"Bucket": bucket.bucket, "Key": key}
            )
        assert bucket.prune(now) == 2
        stub.assert_no_pending_responses()


def test_backup_upload_and_download_use_private_s3_operations(tmp_path):
    path = tmp_path / "backup.zip"
    manifest = archive(path)
    bucket = BackupBucket(settings())
    with Stubber(bucket.client) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": bucket.bucket,
                "Key": ANY,
                "Body": ANY,
                "ContentMD5": ANY,
                "ContentType": "application/zip",
                "Metadata": {
                    "database-identity": manifest.database_identity,
                    "created-at": manifest.created_at.isoformat(),
                },
            },
        )
        stub.add_response(
            "head_object",
            {"ContentLength": path.stat().st_size},
            {"Bucket": bucket.bucket, "Key": ANY},
        )
        key = bucket.put(path, manifest)
        data = path.read_bytes()
        stub.add_response(
            "get_object",
            {
                "ContentLength": len(data),
                "Body": StreamingBody(io.BytesIO(data), len(data)),
            },
            {"Bucket": bucket.bucket, "Key": key},
        )
        assert bucket.download(key, tmp_path / "download.zip") == manifest
        stub.assert_no_pending_responses()


def production(**overrides):
    args = dict(
        _env_file=None,
        database_url="postgresql://owner:secret@db.invalid/db?sslmode=verify-full",
        session_secret="s" * 48,
        session_secure=True,
        allowed_origins=["https://career.onrender.com"],
        openai_api_key="synthetic-key",
        document_backend="s3",
        s3_endpoint="https://originals.invalid",
        s3_bucket="private",
        s3_access_key="key",
        s3_secret_key="secret",
    )
    args.update(overrides)
    return Settings(**args)


@pytest.mark.parametrize(
    "changes",
    [
        {"session_secure": False},
        {"session_secret": None},
        {"allowed_origins": ["http://career.invalid"]},
        {"allowed_origins": ["https://career.invalid/path"]},
        {"database_url": "postgresql://owner:secret@db.invalid/db?sslmode=require"},
        {"document_backend": "local"},
        {"openai_api_key": None},
    ],
)
def test_production_preflight_rejects_unsafe_settings(changes):
    with pytest.raises(BackupError):
        validate_production(production(**changes))


def test_production_configuration_and_sanitized_cli_errors(monkeypatch, capsys):
    validate_production(production())
    monkeypatch.setenv(
        "CAREER_RESTORE_DATABASE_URL",
        "postgresql://owner:private-password@remote.invalid/db",
    )
    with pytest.raises(SystemExit):
        main(["restore", "does-not-exist.zip", "--documents-directory", "/tmp/unused"])
    assert "private-password" not in capsys.readouterr().err


def test_recovery_uses_only_explicit_replacement_storage(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from career_assistant import operations

    monkeypatch.setenv("CAREER_RESTORE_DATABASE_URL", "postgresql://localhost/empty")
    monkeypatch.setenv("AWS_ENDPOINT_URL_S3", "https://live.invalid")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "live-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "live-secret")
    monkeypatch.setenv("CAREER_S3_ENDPOINT", "https://legacy-live.invalid")
    for suffix in ("ENDPOINT", "REGION", "BUCKET", "ACCESS_KEY", "SECRET_KEY"):
        monkeypatch.delenv(f"CAREER_RESTORE_S3_{suffix}", raising=False)
    with pytest.raises(SystemExit) as error:
        main(["restore", str(tmp_path / "backup.zip")])
    assert error.value.code == 1

    replacement = dict(
        ENDPOINT="https://replacement.invalid",
        REGION="eu-central-1",
        BUCKET="replacement",
        ACCESS_KEY="replacement-key",
        SECRET_KEY="replacement-secret",
    )
    for suffix, value in replacement.items():
        monkeypatch.setenv(f"CAREER_RESTORE_S3_{suffix}", value)
    restored = []

    def restore(path, target, store):
        restored.append(store)
        assert store.client.meta.endpoint_url == replacement["ENDPOINT"]
        assert store.client.meta.region_name == replacement["REGION"]
        assert store.bucket == replacement["BUCKET"]
        credentials = store.client._request_signer._credentials.get_frozen_credentials()
        assert credentials.access_key == replacement["ACCESS_KEY"]
        assert credentials.secret_key == replacement["SECRET_KEY"]
        return SimpleNamespace(originals=[], revision="0005")

    monkeypatch.setattr(operations, "restore_archive", restore)
    main(["restore", str(tmp_path / "backup.zip")])
    assert len(restored) == 1


@pytest.mark.parametrize("failure", ["upload", "readback", None])
def test_daily_job_prunes_only_after_successful_readback(
    tmp_path, monkeypatch, failure
):
    from types import SimpleNamespace

    from career_assistant import operations

    calls = []

    def create(sessions, url, store, path):
        return archive(path)

    class Bucket:
        def put(self, path, manifest):
            calls.append("upload")
            self.path, self.manifest = path, manifest
            if failure == "upload":
                raise OSError("synthetic upload failure")
            return "completed.zip"

        def download(self, key, path):
            calls.append("readback")
            if failure == "readback":
                raise BackupError("synthetic readback failure")
            path.write_bytes(self.path.read_bytes())
            return validate_archive(path)

        def prune(self, now):
            calls.append("prune")
            return 1

    monkeypatch.setattr(operations, "BackupBucket", lambda settings: Bucket())
    monkeypatch.setattr(
        operations, "database_engine", lambda url: SimpleNamespace(dispose=lambda: None)
    )
    monkeypatch.setattr(operations, "sessionmaker", lambda engine: None)
    monkeypatch.setattr(operations, "document_store", lambda settings: object())
    monkeypatch.setattr(operations, "create_archive", create)
    if failure:
        with pytest.raises((OSError, BackupError)):
            operations.run_backup(settings())
        assert "prune" not in calls
    else:
        assert operations.run_backup(settings())["expired_removed"] == 1
        assert calls == ["upload", "readback", "prune"]


def test_render_preflight_derives_the_exact_origin_without_logging_secrets(
    monkeypatch, capsys
):
    import json
    import os

    from career_assistant import operations

    monkeypatch.delenv("CAREER_ALLOWED_ORIGINS", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://career.onrender.com")
    monkeypatch.setattr(
        operations,
        "Settings",
        lambda: production(
            allowed_origins=json.loads(os.environ["CAREER_ALLOWED_ORIGINS"])
        ),
    )
    monkeypatch.setattr(operations, "verify_ready", lambda settings: None)
    main(["preflight"])
    result = capsys.readouterr().out
    assert "production_preflight_passed" in result
    assert "synthetic-key" not in result
