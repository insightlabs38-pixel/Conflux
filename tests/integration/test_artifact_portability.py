import hashlib
import io
import json
import os
import uuid
from unittest.mock import patch

import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactStatus
from artifacts.portability import copy_event_artifacts
from artifacts.storage import S3Storage
from botocore.exceptions import ClientError
from django.core.management import call_command
from django.core.management.base import CommandError
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class Store:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.bucket = "artifacts"
        self.objects = {}
        self.writes = []
        self.corrupt = False
        self.bucket_creations = 0

    def ensure_bucket(self):
        self.bucket_creations += 1

    def head(self, key):
        if key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "HeadObject")
        return self.objects[key][1].copy()

    def get(self, key):
        return {**self.head(key), "Body": io.BytesIO(self.objects[key][0])}

    def put(self, key, data, *, content_type, metadata, only_if_absent=False):
        if only_if_absent and key in self.objects:
            raise ClientError({"Error": {"Code": "PreconditionFailed"}}, "PutObject")
        payload = data.read() if hasattr(data, "read") else data
        if self.corrupt:
            payload = b"x" * len(payload)
        self.objects[key] = (
            payload,
            {
                "ContentLength": len(payload),
                "ContentType": content_type,
                "Metadata": metadata.copy(),
            },
        )
        self.writes.append((key, only_if_absent))


@pytest.fixture
def stored():
    workspace = Workspace.objects.create(name="Portable", slug="portable")
    event = Event.objects.create(workspace=workspace, name="Event", slug="portable")
    user = User.objects.create_user(username="participant")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    artifact = Artifact.objects.create(
        project=project,
        created_by=user,
        kind="file",
        visibility="participant",
        content_type="application/pdf",
        byte_size=4,
        status=ArtifactStatus.READY,
        sha256=hashlib.sha256(b"data").hexdigest(),
    )
    artifact.object_key = (
        f"events/{event.public_id}/projects/{project.public_id}/artifacts/{artifact.public_id}/file"
    )
    artifact.save()
    source, destination = Store("https://source.example"), Store("https://destination.example")
    source.put(
        artifact.object_key,
        b"data",
        content_type=artifact.content_type,
        metadata={"artifact-id": str(artifact.public_id), "custom": "preserved"},
    )
    return event, artifact, source, destination


def test_preview_is_read_only_and_copy_preserves_identity_then_retries(stored):
    event, artifact, source, destination = stored
    before = Artifact.objects.values().get(pk=artifact.pk)
    preview = copy_event_artifacts(event, source, destination)
    assert preview["artifacts"][0]["status"] == "would_copy"
    assert destination.objects == {} and destination.bucket_creations == 0
    assert (
        copy_event_artifacts(event, source, destination, execute=True)["artifacts"][0]["status"]
        == "copied"
    )
    assert source.objects == destination.objects
    assert destination.writes == [(artifact.object_key, True)]
    assert (
        copy_event_artifacts(event, source, destination, execute=True)["artifacts"][0]["status"]
        == "verified_existing"
    )
    assert len(destination.writes) == 1
    assert Artifact.objects.values().get(pk=artifact.pk) == before


@pytest.mark.parametrize("field", ["ContentLength", "ContentType", "Metadata", "hash", "key"])
def test_invalid_source_is_never_copied(stored, field):
    event, artifact, source, destination = stored
    if field == "hash":
        artifact.sha256 = "0" * 64
        artifact.save()
    elif field == "key":
        artifact.object_key = "events/another-event/artifacts/file"
        artifact.save()
    else:
        source.objects[artifact.object_key][1][field] = {} if field == "Metadata" else "wrong"
    with pytest.raises(ValueError):
        copy_event_artifacts(event, source, destination, execute=True)
    assert destination.objects == {}


@pytest.mark.parametrize("field", ["content", "metadata"])
def test_destination_collision_never_overwrites(stored, field):
    event, artifact, source, destination = stored
    destination.put(
        artifact.object_key,
        b"data",
        content_type=artifact.content_type,
        metadata=source.head(artifact.object_key)["Metadata"],
    )
    if field == "content":
        destination.objects[artifact.object_key] = (b"evil", destination.head(artifact.object_key))
    else:
        destination.objects[artifact.object_key][1]["Metadata"] = {"artifact-id": "someone else"}
    before = destination.get(artifact.object_key)["Body"].read()
    with pytest.raises(ValueError, match="collision"):
        copy_event_artifacts(event, source, destination, execute=True)
    assert destination.get(artifact.object_key)["Body"].read() == before
    assert len(destination.writes) == 1


def test_destination_corruption_is_not_reported_as_success(stored):
    event, artifact, source, destination = stored
    destination.corrupt = True
    with pytest.raises(ValueError, match="verification failed"):
        copy_event_artifacts(event, source, destination, execute=True)
    with pytest.raises(ValueError, match="collision"):
        copy_event_artifacts(event, source, destination, execute=True)
    assert source.get(artifact.object_key)["Body"].read() == b"data"


def test_access_denied_does_not_become_missing_or_trigger_write(stored):
    event, _, source, destination = stored
    with patch.object(
        destination,
        "head",
        side_effect=ClientError({"Error": {"Code": "AccessDenied"}}, "HeadObject"),
    ):
        with pytest.raises(ClientError):
            copy_event_artifacts(event, source, destination, execute=True)
    assert destination.objects == {}


def test_external_pending_and_other_event_artifacts_are_excluded(stored):
    event, artifact, source, destination = stored
    Artifact.objects.create(
        project=artifact.project,
        created_by=artifact.created_by,
        kind="repository",
        external_url="https://example.com/repo",
    )
    Artifact.objects.create(project=artifact.project, created_by=artifact.created_by, kind="file")
    other_event = Event.objects.create(workspace=event.workspace, name="Other", slug="other")
    other_project = create_project(other_event, artifact.created_by, "Other")
    Artifact.objects.create(
        project=other_project,
        created_by=artifact.created_by,
        kind="file",
        object_key="not-the-target-event",
    )
    assert len(copy_event_artifacts(event, source, destination)["artifacts"]) == 1


def test_same_namespace_is_rejected(stored):
    event, _, source, _ = stored
    with pytest.raises(ValueError, match="different storage"):
        copy_event_artifacts(event, source, source, execute=True)


def test_source_stream_interruption_closes_body_and_never_writes(stored):
    event, artifact, source, destination = stored
    body = io.BytesIO(b"data")
    response = {**source.head(artifact.object_key), "Body": body}
    with (
        patch.object(source, "get", return_value=response),
        patch.object(body, "read", side_effect=TimeoutError("interrupted download")),
    ):
        with pytest.raises(TimeoutError):
            copy_event_artifacts(event, source, destination, execute=True)
    assert body.closed
    assert destination.objects == {}


def test_object_created_after_preview_is_protected_by_conditional_write(stored):
    event, artifact, source, destination = stored
    original_put = destination.put

    def race(key, data, **kwargs):
        original_put(key, b"race", content_type=artifact.content_type, metadata={})
        original_put(key, data, **kwargs)

    with patch.object(destination, "put", side_effect=race):
        with pytest.raises(ClientError, match="PreconditionFailed"):
            copy_event_artifacts(event, source, destination, execute=True)
    assert destination.get(artifact.object_key)["Body"].read() == b"race"


def test_empty_object_is_copied_and_verified(stored):
    event, artifact, source, destination = stored
    artifact.byte_size = 0
    artifact.sha256 = hashlib.sha256(b"").hexdigest()
    artifact.save()
    source.put(
        artifact.object_key,
        b"",
        content_type=artifact.content_type,
        metadata={"artifact-id": str(artifact.public_id)},
    )
    result = copy_event_artifacts(event, source, destination, execute=True)
    assert result["artifacts"][0]["bytes"] == 0
    assert destination.get(artifact.object_key)["Body"].read() == b""


def test_command_requires_private_credentials_and_emits_json(stored, monkeypatch):
    event, _, source, destination = stored
    options = {
        "destination_endpoint": destination.endpoint,
        "destination_bucket": destination.bucket,
    }
    monkeypatch.delenv("CONFLUX_COPY_DEST_ACCESS_KEY", raising=False)
    with pytest.raises(CommandError, match="Set CONFLUX"):
        call_command("copy_event_artifacts", str(event.public_id), **options)
    monkeypatch.setenv("CONFLUX_COPY_DEST_ACCESS_KEY", "private-access")
    monkeypatch.setenv("CONFLUX_COPY_DEST_SECRET_KEY", "private-secret")
    output = io.StringIO()
    with patch(
        "artifacts.management.commands.copy_event_artifacts.S3Storage",
        side_effect=[source, destination],
    ):
        call_command("copy_event_artifacts", str(event.public_id), stdout=output, **options)
    assert not json.loads(output.getvalue())["executed"]
    assert "private-secret" not in output.getvalue()
    with pytest.raises(CommandError):
        call_command("copy_event_artifacts", "not-a-uuid", **options)


@pytest.mark.skipif(
    not os.environ.get("CONFLUX_S3_COPY_SOURCE_ENDPOINT")
    or not os.environ.get("CONFLUX_S3_COPY_DEST_ENDPOINT"),
    reason="Requires two disposable S3-compatible endpoints",
)
def test_real_backend_copy_and_conditional_collision(stored):
    event, artifact, _, _ = stored
    stores = [
        S3Storage(
            endpoint=os.environ[f"CONFLUX_S3_COPY_{name}_ENDPOINT"],
            bucket="conflux-portability-" + uuid.uuid4().hex[:16],
            access_key=os.environ.get(f"CONFLUX_S3_COPY_{name}_ACCESS_KEY", "conflux"),
            secret_key=os.environ.get(f"CONFLUX_S3_COPY_{name}_SECRET_KEY", "conflux-secret"),
        )
        for name in ("SOURCE", "DEST")
    ]
    try:
        for store in stores:
            store.ensure_bucket()
        source, destination = stores
        source.put(
            artifact.object_key,
            b"data",
            content_type=artifact.content_type,
            metadata={"artifact-id": str(artifact.public_id)},
        )
        assert (
            copy_event_artifacts(event, source, destination, execute=True)["artifacts"][0]["status"]
            == "copied"
        )
        assert (
            copy_event_artifacts(event, source, destination, execute=True)["artifacts"][0]["status"]
            == "verified_existing"
        )
        with pytest.raises(ClientError):
            destination.put(artifact.object_key, b"evil", only_if_absent=True)
        assert destination.get(artifact.object_key)["Body"].read() == b"data"
    finally:
        for store in stores:
            for item in store.list_prefix(""):
                store.delete(item["Key"])
            store.client.delete_bucket(Bucket=store.bucket)
