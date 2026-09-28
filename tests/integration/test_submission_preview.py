from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus
from django.test import Client
from django.utils import timezone
from events.models import Event
from projects.services import create_project
from projects.submissions import finalize_submission, save_draft
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class FakeStorage:
    def presign_get(self, key, expires=300, *, download_filename=None):
        return f"https://storage.test/{key}?attachment={download_filename}"


def setup_case():
    workspace = Workspace.objects.create(name="W", slug="w")
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="E",
        slug="e",
        status="open",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
    )
    owner = User.objects.create_user(username="owner", password="unused")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.PARTICIPANT)
    organizer = User.objects.create_user(username="organizer", password="unused")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    judge = User.objects.create_user(username="judge", password="unused")
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    project = create_project(event, owner, "Project")
    stage = Stage.objects.create(event=event, name="Build")
    return project, stage, owner, organizer, judge


def make_artifact(project, owner, *, visibility, key="k/1", body=b"content"):
    import hashlib

    return Artifact.objects.create(
        project=project,
        created_by=owner,
        kind="document",
        visibility=visibility,
        title="Notes",
        object_key=key,
        byte_size=len(body),
        sha256=hashlib.sha256(body).hexdigest(),
        status=ArtifactStatus.READY,
    )


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def base(project, stage):
    return (
        f"/api/v1/workspaces/{project.event.workspace.public_id}/events/"
        f"{project.event.public_id}/projects/{project.public_id}/submissions/"
        f"{stage.public_id}/preview/"
    )


def finalize_with(project, stage, owner, *artifacts):
    save_draft(
        project,
        stage,
        owner,
        payload={"artifact_ids": [str(a.public_id) for a in artifacts]},
        revision=0,
    )
    return finalize_submission(project, stage, owner, revision=1)


def test_preview_404s_until_the_submission_is_finalized():
    project, stage, owner, organizer, judge = setup_case()
    assert client_for(owner).get(base(project, stage)).status_code == 404
    save_draft(project, stage, owner, payload={}, revision=0)
    assert client_for(owner).get(base(project, stage)).status_code == 404


def test_preview_shows_only_judge_visible_frozen_artifacts_to_owner_and_organizer(monkeypatch):
    monkeypatch.setattr("projects.submissions.S3Storage", FakeStorage)
    project, stage, owner, organizer, judge = setup_case()
    visible = make_artifact(project, owner, visibility="judge", key="k/visible")
    hidden = make_artifact(project, owner, visibility="organizer", key="k/hidden")
    finalize_with(project, stage, owner, visible, hidden)

    for user in (owner, organizer):
        response = client_for(user).get(base(project, stage))
        assert response.status_code == 200
        body = response.json()
        assert body["version"] == 1 and body["verified"] is True
        assert [a["id"] for a in body["artifacts"]] == [str(visible.public_id)]
        assert body["artifacts"][0]["drift"] is None
        assert body["artifacts"][0]["download_url"] == "https://storage.test/k/visible?attachment=Notes"

    assert client_for(judge).get(base(project, stage)).status_code == 404
    outsider = User.objects.create_user(username="outsider", password="unused")
    Membership.objects.create(workspace=project.event.workspace, user=outsider, role=Role.PARTICIPANT)
    assert client_for(outsider).get(base(project, stage)).status_code == 404


def test_content_drift_after_finalization_is_flagged_and_blocks_download(monkeypatch):
    monkeypatch.setattr("projects.submissions.S3Storage", FakeStorage)
    project, stage, owner, organizer, judge = setup_case()
    artifact = make_artifact(project, owner, visibility="public", key="k/drift")
    finalize_with(project, stage, owner, artifact)

    Artifact.objects.filter(pk=artifact.pk).update(sha256="0" * 64)
    body = client_for(owner).get(base(project, stage)).json()
    assert body["verified"] is False
    assert body["artifacts"][0]["drift"] == "content_changed"
    assert body["artifacts"][0]["download_url"] is None


def test_removed_artifact_is_flagged_as_drift(monkeypatch):
    monkeypatch.setattr("projects.submissions.S3Storage", FakeStorage)
    project, stage, owner, organizer, judge = setup_case()
    artifact = make_artifact(project, owner, visibility="public", key="k/gone")
    finalize_with(project, stage, owner, artifact)

    artifact.delete()
    body = client_for(owner).get(base(project, stage)).json()
    assert body["verified"] is False
    assert body["artifacts"][0]["drift"] == "removed"
    assert body["artifacts"][0]["download_url"] is None
