import os
import re
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from artifacts.storage import PART_SIZE, S3Storage
from botocore.exceptions import ClientError

ENDPOINT = os.environ.get("CONFLUX_S3_TEST_ENDPOINT")
pytestmark = pytest.mark.skipif(
    not ENDPOINT, reason="Set CONFLUX_S3_TEST_ENDPOINT to run the storage contract"
)


@pytest.fixture
def storage():
    bucket = "conflux-contract-" + uuid.uuid4().hex[:16]
    store = S3Storage(
        endpoint=ENDPOINT,
        public_endpoint=ENDPOINT,
        bucket=bucket,
        access_key=os.environ.get("CONFLUX_S3_TEST_ACCESS_KEY", "conflux"),
        secret_key=os.environ.get("CONFLUX_S3_TEST_SECRET_KEY", "conflux-secret"),
    )
    store.ensure_bucket()
    yield store
    for item in store.list_prefix(""):
        store.delete(item["Key"])
    store.client.delete_bucket(Bucket=bucket)


def read_object(store, key):
    return store.get(key)["Body"].read()


def test_put_get_head_delete_list_overwrite_zero_and_unicode(storage):
    prefix = "contract/" + uuid.uuid4().hex + "/"
    key = prefix + "résumé 雪 + spaces.txt"
    storage.put(key, b"first", content_type="text/plain", metadata={"source": "contract"})
    assert read_object(storage, key) == b"first"
    head = storage.head(key)
    assert head["ContentLength"] == 5
    assert head["ContentType"] == "text/plain"
    assert head["Metadata"]["source"] == "contract"
    assert key in {item["Key"] for item in storage.list_prefix(prefix)}
    storage.put(key, b"second", content_type="text/plain")
    assert read_object(storage, key) == b"second"
    empty_key = prefix + "empty"
    storage.put(empty_key, b"")
    assert storage.head(empty_key)["ContentLength"] == 0
    assert read_object(storage, empty_key) == b""
    storage.delete(key)
    storage.delete(empty_key)
    storage.delete(prefix + "already-missing")
    with pytest.raises(ClientError):
        storage.head(key)


def test_presigned_put_get_signature_and_expiry(storage):
    key = "presigned/" + uuid.uuid4().hex
    artifact_id = str(uuid.uuid4())
    url = storage.presign_put(key, "text/plain", artifact_id, 60)
    headers = {"Content-Type": "text/plain", "x-amz-meta-artifact-id": artifact_id}
    with urllib.request.urlopen(
        urllib.request.Request(url, data=b"signed", method="PUT", headers=headers), timeout=10
    ) as response:
        assert response.status in (200, 201)
    assert storage.head(key)["Metadata"]["artifact-id"] == artifact_id
    with urllib.request.urlopen(storage.presign_get(key, 60), timeout=10) as response:
        assert response.read() == b"signed"
    tampered = re.sub(
        r"(X-Amz-Signature=)[0-9a-f]+",
        lambda match: match.group(1) + "0" * 64,
        storage.presign_get(key, 60),
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(tampered, timeout=10)
    assert exc.value.code in (400, 401, 403)
    expired = storage.presign_get(key, 1)
    time.sleep(2.2)
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(expired, timeout=10)
    assert exc.value.code in (400, 401, 403)


def test_multipart_and_concurrent_independent_uploads(storage):
    key = "multipart/" + uuid.uuid4().hex
    artifact_id = str(uuid.uuid4())
    data = b"a" * PART_SIZE + b"b"
    upload_id, urls = storage.start_multipart(
        key, "application/octet-stream", artifact_id, len(data), 120
    )
    assert len(urls) == 2
    parts = []
    for number, (url, chunk) in enumerate(zip(urls, (data[:PART_SIZE], data[PART_SIZE:])), 1):
        with urllib.request.urlopen(
            urllib.request.Request(url, data=chunk, method="PUT"), timeout=30
        ) as response:
            parts.append({"PartNumber": number, "ETag": response.headers["ETag"]})
    storage.complete_multipart(key, upload_id, parts)
    assert storage.head(key)["ContentLength"] == len(data)
    assert read_object(storage, key) == data

    prefix = "parallel/" + uuid.uuid4().hex + "/"

    def upload_one(number):
        item_key = prefix + str(number)
        payload = f"payload-{number}".encode()
        storage.put(item_key, payload)
        return item_key, read_object(storage, item_key)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(upload_one, range(6)))
    assert all(value == f"payload-{index}".encode() for index, (_, value) in enumerate(results))
    assert len(storage.list_prefix(prefix)) == 6
