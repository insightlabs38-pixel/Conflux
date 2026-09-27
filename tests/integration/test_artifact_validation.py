import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactStatus, ArtifactValidation, ArtifactVisibility
from artifacts.services import create_external_artifact
from artifacts.validators import VALIDATORS, validate_artifact
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class FakeStorage:
    def __init__(self, info=None, error=None):
        self.info = info
        self.error = error

    def head(self, key):
        if self.error:
            raise self.error
        return self.info


def setup_project():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    return create_project(event, user, "Project"), user


def stored_artifact(project, user, *, kind="image", content_type="image/png"):
    return Artifact.objects.create(
        project=project,
        created_by=user,
        kind=kind,
        visibility=ArtifactVisibility.PARTICIPANT,
        title="Proof",
        object_key="proof/key",
        content_type=content_type,
        byte_size=4,
        status=ArtifactStatus.UPLOADED,
    )


def test_registry_covers_every_kind_and_marks_verified_object_ready():
    from artifacts.models import ArtifactKind

    assert set(VALIDATORS) == set(ArtifactKind.values)
    project, user = setup_project()
    artifact = stored_artifact(project, user)
    info = {
        "ContentLength": 4,
        "ContentType": "image/png",
        "Metadata": {"artifact-id": str(artifact.public_id)},
    }
    evidence = validate_artifact(artifact, storage=FakeStorage(info))
    artifact.refresh_from_db()
    assert evidence.outcome == "ok"
    assert artifact.status == ArtifactStatus.READY


def test_wrong_media_type_blocks_and_unavailable_storage_retries():
    project, user = setup_project()
    artifact = stored_artifact(project, user, content_type="application/pdf")
    info = {
        "ContentLength": 4,
        "ContentType": "application/pdf",
        "Metadata": {"artifact-id": str(artifact.public_id)},
    }
    evidence = validate_artifact(artifact, storage=FakeStorage(info))
    assert evidence.outcome == "blocked"
    artifact.refresh_from_db()
    assert artifact.status == ArtifactStatus.REJECTED
    artifact.status = ArtifactStatus.UPLOADED
    artifact.save(update_fields=["status", "updated_at"])
    evidence = validate_artifact(artifact, storage=FakeStorage(error=OSError("temporary")))
    assert evidence.outcome == "retry"
    artifact.refresh_from_db()
    assert artifact.status == ArtifactStatus.UPLOADED


def test_external_links_are_ready_with_explicit_warning_without_network_fetch():
    project, user = setup_project()
    artifact = create_external_artifact(
        project,
        user,
        kind="repository",
        visibility="public",
        title="Repo",
        url="https://example.com/repo",
    )
    evidence = validate_artifact(artifact)
    artifact.refresh_from_db()
    assert evidence.outcome == "warning"
    assert artifact.status == ArtifactStatus.READY
    assert ArtifactValidation.objects.filter(artifact=artifact).count() == 1


def test_pending_upload_remains_unready():
    project, user = setup_project()
    artifact = Artifact.objects.create(
        project=project, created_by=user, kind="file", visibility="participant", title="Pending"
    )
    evidence = validate_artifact(artifact)
    artifact.refresh_from_db()
    assert evidence.outcome == "retry"
    assert artifact.status == ArtifactStatus.PENDING
