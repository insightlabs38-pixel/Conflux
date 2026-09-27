from datetime import timedelta

import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactStatus, ArtifactVisibility
from artifacts.services import begin_upload, complete_upload
from django.core.exceptions import ValidationError
from django.utils import timezone
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class FakeStorage:
    def __init__(self):
        self.info = None

    def ensure_bucket(self):
        pass

    def presign_put(self, key, content_type, artifact_id, expires):
        self.key = key
        self.artifact_id = artifact_id
        self.info = {
            "ContentLength": 4,
            "ContentType": content_type,
            "Metadata": {"artifact-id": artifact_id},
        }
        return "https://upload.example.com/signed"

    def head(self, key):
        assert key == self.key
        return self.info

    def start_multipart(self, key, content_type, artifact_id, size, expires):
        self.key = key
        self.info = {
            "ContentLength": size,
            "ContentType": content_type,
            "Metadata": {"artifact-id": artifact_id},
        }
        return "upload-1", [
            "https://upload.example.com/part-1",
            "https://upload.example.com/part-2",
        ]

    def complete_multipart(self, key, upload_id, parts):
        assert key == self.key
        assert upload_id == "upload-1"
        assert [part["PartNumber"] for part in parts] == [1, 2]


def setup_project():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    return create_project(event, user, "Project"), user


def test_single_part_upload_verifies_storage_metadata_and_replay():
    project, user = setup_project()
    storage = FakeStorage()
    artifact, intent, payload = begin_upload(
        project,
        user,
        kind="file",
        visibility=ArtifactVisibility.PARTICIPANT,
        title="Deck",
        byte_size=4,
        content_type="application/pdf",
        storage=storage,
    )
    assert payload["mode"] == "single"
    assert payload["headers"]["x-amz-meta-artifact-id"] == str(artifact.public_id)
    uploaded = complete_upload(intent, user, storage=storage)
    assert uploaded.status == ArtifactStatus.UPLOADED
    assert uploaded.byte_size == 4
    with pytest.raises(ValidationError, match="already completed"):
        complete_upload(intent, user, storage=storage)


def test_metadata_mismatch_and_closed_window_do_not_mark_ready():
    project, user = setup_project()
    storage = FakeStorage()
    artifact, intent, _ = begin_upload(
        project,
        user,
        kind="file",
        visibility=ArtifactVisibility.PARTICIPANT,
        title="Deck",
        byte_size=4,
        content_type="application/pdf",
        storage=storage,
    )
    storage.info["ContentLength"] = 3
    with pytest.raises(ValidationError, match="does not match"):
        complete_upload(intent, user, storage=storage)
    artifact.refresh_from_db()
    assert artifact.status == ArtifactStatus.PENDING
    project.event.ends_at = timezone.now() - timedelta(seconds=1)
    project.event.save(update_fields=["ends_at"])
    with pytest.raises(ValidationError, match="closed"):
        begin_upload(
            project,
            user,
            kind="file",
            visibility=ArtifactVisibility.PARTICIPANT,
            title="Late",
            byte_size=4,
            content_type="application/pdf",
            storage=storage,
        )


def test_nonmember_cannot_issue_or_complete_upload():
    project, user = setup_project()
    outsider = User.objects.create_user(username="outsider", password="unused")
    storage = FakeStorage()
    with pytest.raises(ValidationError, match="project members"):
        begin_upload(
            project,
            outsider,
            kind="file",
            visibility=ArtifactVisibility.PARTICIPANT,
            title="Deck",
            byte_size=4,
            content_type="application/pdf",
            storage=storage,
        )
    _, intent, _ = begin_upload(
        project,
        user,
        kind="file",
        visibility=ArtifactVisibility.PARTICIPANT,
        title="Deck",
        byte_size=4,
        content_type="application/pdf",
        storage=storage,
    )
    with pytest.raises(ValidationError, match="project members"):
        complete_upload(intent, outsider, storage=storage)
    assert Artifact.objects.count() == 1


def test_multipart_completion_requires_exact_ordered_parts(monkeypatch):
    monkeypatch.setattr("artifacts.services.MULTIPART_THRESHOLD", 1)
    project, user = setup_project()
    storage = FakeStorage()
    _, intent, payload = begin_upload(
        project,
        user,
        kind="video",
        visibility=ArtifactVisibility.PUBLIC,
        title="Demo",
        byte_size=4,
        content_type="video/mp4",
        storage=storage,
    )
    assert payload["mode"] == "multipart"
    with pytest.raises(ValidationError, match="every numbered part"):
        complete_upload(intent, user, parts=[{"PartNumber": 2, "ETag": "x"}], storage=storage)
    artifact = complete_upload(
        intent,
        user,
        parts=[{"PartNumber": 1, "ETag": "a"}, {"PartNumber": 2, "ETag": "b"}],
        storage=storage,
    )
    assert artifact.status == ArtifactStatus.UPLOADED
