"""Private original-document storage; metadata and extracted text stay in Postgres."""

from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from career_assistant.config import Settings
from career_assistant.models import DocumentDeletion


class DocumentStore(Protocol):
    def put(self, key: UUID, content: bytes) -> None: ...

    def get(self, key: UUID) -> bytes: ...

    def delete(self, key: UUID) -> None: ...


class LocalDocumentStore:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def put(self, key: UUID, content: bytes) -> None:
        (self.directory / str(key)).write_bytes(content)

    def get(self, key: UUID) -> bytes:
        return (self.directory / str(key)).read_bytes()

    def delete(self, key: UUID) -> None:
        (self.directory / str(key)).unlink(missing_ok=True)


class NeonDocumentStore:
    """S3 wire protocol only; the caller supplies a client bound to Neon."""

    def __init__(self, client, bucket: str):
        self.client = client
        self.bucket = bucket

    def put(self, key: UUID, content: bytes) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=f"documents/{key}",
            Body=content,
            ContentType="application/octet-stream",
        )

    def get(self, key: UUID) -> bytes:
        try:
            response = self.client.get_object(
                Bucket=self.bucket, Key=f"documents/{key}"
            )
        except ClientError as error:
            if error.response["Error"]["Code"] in {"NoSuchKey", "404"}:
                raise FileNotFoundError(str(key)) from None
            raise
        with response["Body"] as body:
            return body.read()

    def delete(self, key: UUID) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=f"documents/{key}")


def document_store(settings: Settings) -> DocumentStore:
    if settings.document_backend == "local":
        return LocalDocumentStore(settings.document_directory)
    if not all(
        (
            settings.neon_storage_endpoint,
            settings.neon_storage_bucket,
            settings.neon_storage_access_key,
            settings.neon_storage_secret_key,
        )
    ):
        raise ValueError("Neon storage requires an endpoint, bucket, and credentials")
    endpoint = urlsplit(settings.neon_storage_endpoint)
    if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username:
        raise ValueError("Neon storage requires an HTTPS endpoint without credentials")
    client = boto3.client(
        "s3",
        endpoint_url=settings.neon_storage_endpoint,
        region_name=settings.neon_storage_region,
        aws_access_key_id=settings.neon_storage_access_key.get_secret_value(),
        aws_secret_access_key=settings.neon_storage_secret_key.get_secret_value(),
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 2},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )
    return NeonDocumentStore(client, settings.neon_storage_bucket)


def cleanup_documents(sessions: sessionmaker, store: DocumentStore) -> int:
    """Call after committing metadata deletion; failed object deletions stay queued."""
    with sessions.begin() as session:
        pending = list(
            session.scalars(
                select(DocumentDeletion)
                .order_by(DocumentDeletion.created_at)
                .limit(100)
                .with_for_update(skip_locked=True)
            )
        )
        for item in pending:
            store.delete(item.object_key)
            session.delete(item)
        return len(pending)
