from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus
from artifacts.preflight import run_preflight
from artifacts.services import create_external_artifact
from artifacts.validators import validate_artifact
from django.test import Client
from django.utils import timezone
from events.models import Event
from forms.services import create_form, publish_form, save_draft, save_response
from policies.models import Action, Policy, PolicyBinding, TemporalGate
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_project():
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
    return create_project(event, user, "Project"), user


def test_preflight_ready_warning_and_pending_artifact():
    project, user = setup_project()
    assert run_preflight(project).status == "READY"
    artifact = create_external_artifact(
        project,
        user,
        kind="repository",
        visibility="public",
        title="Repo",
        url="https://example.com/repo",
    )
    assert run_preflight(project).status == "BLOCKED"
    validate_artifact(artifact)
    result = run_preflight(project)
    assert result.status == "WARNING"
    assert result.checks[0].code == "artifact_warning"
    Artifact.objects.create(
        project=project, created_by=user, kind="file", visibility="participant", title="Pending"
    )
    assert "artifact_not_ready" in {check.code for check in run_preflight(project).checks}


def test_preflight_requires_published_form_answers_and_ready_references():
    project, user = setup_project()
    form = create_form(project.event, "Application")
    assert "form_unpublished" in {check.code for check in run_preflight(project).checks}
    save_draft(
        form,
        {
            "fields": [
                {"id": "pitch", "type": "text", "label": "Pitch", "required": True},
                {"id": "proof", "type": "artifact", "label": "Proof", "required": True},
            ]
        },
    )
    version = publish_form(form)
    assert "form_missing" in {check.code for check in run_preflight(project).checks}
    artifact = Artifact.objects.create(
        project=project,
        created_by=user,
        kind="file",
        visibility="participant",
        title="Proof",
        status=ArtifactStatus.PENDING,
    )
    save_response(project, version, user, {"pitch": "Idea", "proof": str(artifact.public_id)})
    codes = {check.code for check in run_preflight(project).checks}
    assert {"artifact_reference", "artifact_not_ready"} <= codes


def test_preflight_checks_policy_gate_and_authoritative_deadline():
    project, user = setup_project()
    gate = TemporalGate.objects.create(
        event=project.event, name="submissions", closes_at=timezone.now() - timedelta(minutes=1)
    )
    policy = Policy.objects.create(
        event=project.event,
        name="Window",
        ast={"op": "eq", "fact": f"gate_open:{gate.name}", "value": True},
    )
    PolicyBinding.objects.create(event=project.event, action=Action.SUBMIT, policy=policy)
    assert "submit_policy" in {check.code for check in run_preflight(project).checks}
    project.event.ends_at = timezone.now() - timedelta(seconds=1)
    project.event.save(update_fields=["ends_at"])
    assert "event_deadline" in {check.code for check in run_preflight(project).checks}
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    url = (
        f"/api/v1/workspaces/{project.event.workspace.public_id}/events/{project.event.public_id}/"
        f"projects/{project.public_id}/artifacts/preflight/"
    )
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"
