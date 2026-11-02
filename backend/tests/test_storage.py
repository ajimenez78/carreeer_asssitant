import io
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from botocore.stub import Stubber

from career_assistant.config import Settings
from career_assistant.storage import (
    LocalDocumentStore,
    S3DocumentStore,
    document_store,
)


def test_local_originals_are_private_and_deletion_is_idempotent(tmp_path):
    store = document_store(
        Settings(_env_file=None, document_directory=tmp_path / "private")
    )
    assert isinstance(store, LocalDocumentStore)
    key = uuid4()
    store.put(key, b"Synthetic original, not a real CV.")
    assert store.get(key) == b"Synthetic original, not a real CV."
    assert store.directory.stat().st_mode & 0o777 == 0o700
    assert [item.name for item in store.directory.iterdir()] == [str(key)]
    store.delete(key)
    store.delete(key)
    with pytest.raises(FileNotFoundError):
        store.get(key)


def s3_settings(**overrides):
    values = dict(
        document_backend="s3",
        s3_endpoint="https://storage.example.invalid",
        s3_bucket="private-documents",
        s3_access_key="synthetic-key",
        s3_secret_key="synthetic-secret",
    )
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_s3_client_uses_only_supported_private_object_operations():
    store = document_store(s3_settings())
    assert isinstance(store, S3DocumentStore)
    assert store.client.meta.config.s3["addressing_style"] == "path"
    assert store.client.meta.config.signature_version == "s3v4"
    assert store.client.meta.endpoint_url == "https://storage.example.invalid"
    key = uuid4()
    params = {"Bucket": "private-documents", "Key": f"documents/{key}"}
    body = StreamingBody(io.BytesIO(b"synthetic"), 9)
    with Stubber(store.client) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                **params,
                "Body": b"synthetic",
                "ContentType": "application/octet-stream",
            },
        )
        stub.add_response("get_object", {"Body": body}, params)
        stub.add_response("delete_object", {}, params)
        store.put(key, b"synthetic")
        assert store.get(key) == b"synthetic"
        store.delete(key)
        stub.assert_no_pending_responses()


def test_s3_missing_objects_and_provider_failure():
    store = document_store(s3_settings())
    key = uuid4()
    params = {"Bucket": "private-documents", "Key": f"documents/{key}"}
    with Stubber(store.client) as stub:
        stub.add_client_error("get_object", "NoSuchKey", expected_params=params)
        stub.add_client_error("get_object", "AccessDenied", expected_params=params)
        with pytest.raises(FileNotFoundError):
            store.get(key)
        with pytest.raises(ClientError):
            store.get(key)


@pytest.mark.parametrize(
    "overrides",
    [
        {"s3_access_key": None},
        {"s3_endpoint": "http://storage.example.invalid"},
        {"s3_endpoint": "https://user:password@storage.example.invalid"},
    ],
)
def test_incomplete_or_insecure_s3_configuration_is_rejected(overrides):
    with pytest.raises(ValueError):
        document_store(s3_settings(**overrides))
