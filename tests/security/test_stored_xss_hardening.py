"""GSEC-002: a stored artifact is served from this application's own origin
(infra/Caddyfile reverse-proxies the object store under the same host as
the app -- see docs/architecture/ARTIFACT_SERVING.md), so an uploader's
claimed `content_type` can never be trusted enough to render inline. Two
independent layers close this: `presign_get` always forces
`Content-Disposition: attachment`, and validation outright rejects a
handful of content types a browser would actively execute/render,
regardless of the artifact's `kind`.
"""

import urllib.parse

import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactStatus, ArtifactVisibility
from artifacts.storage import S3Storage
from artifacts.validators import validate_artifact
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class FakeStorage:
    def __init__(self, info):
        self.info = info

    def head(self, key):
        return self.info


def setup_project():
    workspace = Workspace.objects.create(name="Sec", slug="sec")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="uploader", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    return create_project(event, user, "Project"), user


def stored_artifact(project, user, *, kind, content_type):
    return Artifact.objects.create(
        project=project,
        created_by=user,
        kind=kind,
        visibility=ArtifactVisibility.PUBLIC,
        title="Evidence",
        object_key="proof/key",
        content_type=content_type,
        byte_size=4,
        status=ArtifactStatus.UPLOADED,
    )


@pytest.mark.parametrize(
    "kind,content_type",
    [
        ("file", "text/html"),
        ("document", "text/html"),
        ("dataset", "application/xhtml+xml"),
        ("image", "image/svg+xml"),  # passes a naive "image/*" prefix check; must still be blocked
    ],
)
def test_active_content_types_are_rejected_for_every_kind(kind, content_type):
    project, user = setup_project()
    artifact = stored_artifact(project, user, kind=kind, content_type=content_type)
    info = {
        "ContentLength": 4,
        "ContentType": content_type,
        "Metadata": {"artifact-id": str(artifact.public_id)},
    }
    evidence = validate_artifact(artifact, storage=FakeStorage(info))
    artifact.refresh_from_db()
    assert evidence.outcome == "blocked"
    assert artifact.status == ArtifactStatus.REJECTED


def test_ordinary_file_content_type_still_passes():
    project, user = setup_project()
    artifact = stored_artifact(project, user, kind="file", content_type="application/pdf")
    info = {
        "ContentLength": 4,
        "ContentType": "application/pdf",
        "Metadata": {"artifact-id": str(artifact.public_id)},
    }
    evidence = validate_artifact(artifact, storage=FakeStorage(info))
    artifact.refresh_from_db()
    assert evidence.outcome == "ok"
    assert artifact.status == ArtifactStatus.READY


def test_presigned_download_always_forces_attachment_disposition():
    storage = S3Storage(
        endpoint="http://localhost:9000",
        public_endpoint="http://localhost:9000",
        bucket="b",
        access_key="a",
        secret_key="s",
    )
    url = storage.presign_get("some/key", 60, download_filename='evil".txt\r\nX-Injected: 1')
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    disposition = query["response-content-disposition"][0]
    assert disposition == 'attachment; filename="evil.txtX-Injected: 1"'
    # A quote/CR/LF in the artifact title can never break out of the
    # filename value or inject a second header/line into the response.
    assert "\r" not in disposition and "\n" not in disposition
    assert disposition.count('"') == 2
