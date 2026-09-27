from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus
from audit.models import AuditEvent, DomainEvent
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from events.models import Event
from forms.services import create_form, publish_form, save_response
from forms.services import save_draft as save_form_draft
from policies.models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from projects.models import Submission, SubmissionVersion
from projects.services import create_project
from projects.submissions import finalize_submission, save_draft
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


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
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    stage = Stage.objects.create(event=event, name="Build")
    return project, stage, user


def test_draft_revision_and_finalization_receipt_are_idempotent():
    project, stage, user = setup_case()
    draft = save_draft(project, stage, user, payload={"notes": "First"}, revision=0)
    assert draft.draft_revision == 1
    with pytest.raises(ValidationError, match="stale"):
        save_draft(project, stage, user, payload={"notes": "Lost"}, revision=0)
    artifact = Artifact.objects.create(
        project=project,
        created_by=user,
        kind="repository",
        visibility="public",
        title="Repo",
        external_url="https://example.com/repo",
        status=ArtifactStatus.READY,
    )
    draft = save_draft(
        project,
        stage,
        user,
        payload={"notes": "Final", "artifact_ids": [str(artifact.public_id)]},
        revision=1,
    )
    submission, version, created = finalize_submission(project, stage, user, revision=2)
    assert created and submission.current_version == version
    assert version.snapshot["draft"]["notes"] == "Final"
    assert version.snapshot["artifacts"][0]["id"] == str(artifact.public_id)
    assert len(version.digest) == 64
    retry, same, created = finalize_submission(project, stage, user, revision=2)
    assert not created and retry.pk == submission.pk and same.pk == version.pk
    assert SubmissionVersion.objects.count() == 1
    assert AuditEvent.objects.filter(action="submission.finalized").count() == 1
    assert DomainEvent.objects.filter(event_type="submission.finalized").count() == 1
    with pytest.raises(ValidationError, match="finalized"):
        save_draft(project, stage, user, payload={}, revision=2)


def test_blocked_preflight_rolls_back_and_wrong_artifact_cannot_be_frozen():
    project, stage, user = setup_case()
    other = create_project(project.event, user, "Other")
    alien = Artifact.objects.create(
        project=other,
        created_by=user,
        kind="repository",
        visibility="public",
        title="Alien",
        external_url="https://example.com/alien",
        status=ArtifactStatus.READY,
    )
    save_draft(project, stage, user, payload={"artifact_ids": [str(alien.public_id)]}, revision=0)
    with pytest.raises(ValidationError, match="missing"):
        finalize_submission(project, stage, user, revision=1)
    assert Submission.objects.get(project=project).status == "draft"
    assert not SubmissionVersion.objects.exists()
    assert not DomainEvent.objects.filter(event_type="submission.finalized").exists()


def test_finalized_form_answers_are_frozen_and_not_exposed_in_member_receipt():
    project, stage, user = setup_case()
    form = create_form(project.event, "Application")
    save_form_draft(
        form, {"fields": [{"id": "pitch", "type": "text", "label": "Pitch", "required": True}]}
    )
    form_version = publish_form(form)
    save_response(project, form_version, user, {"pitch": "Original"})
    save_draft(project, stage, user, payload={}, revision=0)
    _, version, _ = finalize_submission(project, stage, user, revision=1)
    save_response(project, form_version, user, {"pitch": "Changed"})
    version.refresh_from_db()
    assert version.snapshot["forms"][0]["answers"] == {"pitch": "Original"}
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    base = (
        f"/api/v1/workspaces/{project.event.workspace.public_id}/events/"
        f"{project.event.public_id}/projects/{project.public_id}/submissions/{stage.public_id}/"
    )
    response = client.get(base)
    assert response.status_code == 200
    assert "snapshot" not in response.json()["versions"][0]


def test_policy_grant_does_not_override_hard_event_deadline():
    project, stage, user = setup_case()
    gate = TemporalGate.objects.create(
        event=project.event, name="submissions", closes_at=timezone.now() - timedelta(minutes=1)
    )
    policy = Policy.objects.create(
        event=project.event,
        name="Window",
        ast={"op": "eq", "fact": f"gate_open:{gate.name}", "value": True},
    )
    PolicyBinding.objects.create(event=project.event, action=Action.SUBMIT, policy=policy)
    with pytest.raises(ValidationError, match="Denied"):
        save_draft(project, stage, user, payload={}, revision=0)
    ExceptionGrant.objects.create(
        event=project.event,
        action=Action.SUBMIT,
        subject_type="project",
        subject_id=str(project.public_id),
        reason="Extra time",
        granted_by=user,
    )
    save_draft(project, stage, user, payload={}, revision=0)
    project.event.ends_at = timezone.now() - timedelta(seconds=1)
    project.event.save(update_fields=["ends_at"])
    with pytest.raises(ValidationError, match="deadline"):
        finalize_submission(project, stage, user, revision=1)


def test_submission_api_scopes_project_and_returns_history():
    project, stage, user = setup_case()
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    base = (
        f"/api/v1/workspaces/{project.event.workspace.public_id}/events/"
        f"{project.event.public_id}/projects/{project.public_id}/submissions/"
    )
    assert client.get(base).json()[0]["submission"] is None
    saved = client.put(
        base + f"{stage.public_id}/",
        {"draft_payload": {"notes": "Ready"}, "draft_revision": 0},
        content_type="application/json",
    )
    assert saved.status_code == 200
    assert saved.json()["draft_revision"] == 1
    assert (
        client.put(
            base + f"{stage.public_id}/",
            {"draft_payload": {}, "draft_revision": 0},
            content_type="application/json",
        ).status_code
        == 400
    )
    finalized = client.post(
        base + f"{stage.public_id}/finalize/",
        {"draft_revision": 1},
        content_type="application/json",
    )
    assert finalized.status_code == 201
    receipt = finalized.json()["receipt"]
    assert finalized.json()["submission"]["versions"][0]["public_id"] == receipt
    assert (
        client.post(
            base + f"{stage.public_id}/finalize/",
            {"draft_revision": 1},
            content_type="application/json",
        ).status_code
        == 200
    )
    outsider = User.objects.create_user(username="outsider", password="unused")
    Membership.objects.create(
        workspace=project.event.workspace, user=outsider, role=Role.PARTICIPANT
    )
    client.cookies["session"] = Session.issue(outsider).token
    assert client.get(base).status_code == 404
