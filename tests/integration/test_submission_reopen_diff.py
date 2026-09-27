from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus
from audit.models import AuditEvent
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from events.models import Event
from projects.models import SubmissionStatus
from projects.services import create_project
from projects.submissions import finalize_submission, reopen_submission, save_draft
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def setup_case():
    workspace = Workspace.objects.create(name="W", slug="w")
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="E",
        slug="e",
        status="open",
        starts_at=now - timedelta(days=2),
        ends_at=now + timedelta(days=1),
    )
    organizer = User.objects.create_user(username="organizer", password="unused")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    member = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=member, role=Role.PARTICIPANT)
    project = create_project(event, member, "Project")
    stage = Stage.objects.create(event=event, name="Build")
    return workspace, event, project, stage, organizer, member


def finalize_once(project, stage, user, *, notes="First"):
    artifact = Artifact.objects.create(
        project=project,
        created_by=user,
        kind="repository",
        visibility="public",
        title="Repo",
        external_url="https://example.com/repo",
        status=ArtifactStatus.READY,
    )
    save_draft(
        project,
        stage,
        user,
        payload={"notes": notes, "artifact_ids": [str(artifact.public_id)]},
        revision=0,
    )
    submission, version, _ = finalize_submission(project, stage, user, revision=1)
    return submission, version


def url(workspace, event, project, stage, suffix):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/projects/{project.public_id}/submissions/{stage.public_id}/{suffix}"
    )


def test_reopen_moves_a_finalized_submission_back_to_draft_and_records_an_audit_event():
    workspace, event, project, stage, organizer, member = setup_case()
    finalize_once(project, stage, member)

    submission = reopen_submission(project, stage, organizer, reason="wrong demo link")
    assert submission.status == SubmissionStatus.DRAFT
    assert submission.current_version is not None  # history preserved
    assert AuditEvent.objects.filter(action="submission.reopened").count() == 1


def test_reopen_raises_for_a_submission_that_is_not_finalized():
    _, _, project, stage, organizer, member = setup_case()
    save_draft(project, stage, member, payload={"notes": "still drafting"}, revision=0)
    with pytest.raises(ValidationError, match="finalized"):
        reopen_submission(project, stage, organizer)


def test_reopen_service_rejects_non_organizers_without_changing_history():
    _, _, project, stage, organizer, member = setup_case()
    submission, first_version = finalize_once(project, stage, member)
    with pytest.raises(ValidationError, match="organizers"):
        reopen_submission(project, stage, member)
    submission.refresh_from_db()
    assert submission.status == SubmissionStatus.FINALIZED
    assert submission.current_version_id == first_version.pk
    assert AuditEvent.objects.filter(action="submission.reopened").count() == 0


def test_reopened_submission_can_be_refinalized_within_the_window_producing_a_new_version():
    _, _, project, stage, organizer, member = setup_case()
    submission, first_version = finalize_once(project, stage, member, notes="First")
    reopen_submission(project, stage, organizer)

    save_draft(project, stage, member, payload={"notes": "Fixed", "artifact_ids": []}, revision=1)
    submission, second_version, created = finalize_submission(project, stage, member, revision=2)
    assert created
    assert second_version.number == first_version.number + 1
    assert submission.versions.count() == 2
    first_version.refresh_from_db()
    assert first_version.snapshot["draft"]["notes"] == "First"


def test_reopen_cannot_bypass_the_submission_deadline():
    _, _, project, stage, organizer, member = setup_case()
    submission, first_version = finalize_once(project, stage, member)
    project.event.ends_at = timezone.now() - timedelta(minutes=1)
    project.event.save(update_fields=["ends_at"])
    with pytest.raises(ValidationError, match="deadline"):
        reopen_submission(project, stage, organizer)
    submission.refresh_from_db()
    assert submission.status == SubmissionStatus.FINALIZED
    assert submission.current_version_id == first_version.pk


def test_reopened_draft_cannot_be_saved_after_the_deadline():
    _, _, project, stage, organizer, member = setup_case()
    submission, first_version = finalize_once(project, stage, member)
    reopen_submission(project, stage, organizer)
    project.event.ends_at = timezone.now() - timedelta(minutes=1)
    project.event.save(update_fields=["ends_at"])
    with pytest.raises(ValidationError, match="deadline"):
        save_draft(project, stage, member, payload={"notes": "late"}, revision=1)
    with pytest.raises(ValidationError, match="deadline"):
        finalize_submission(project, stage, member, revision=1)
    submission.refresh_from_db()
    assert submission.current_version_id == first_version.pk
    assert submission.versions.count() == 1


def test_reopen_endpoint_validates_reason_and_records_it():
    workspace, event, project, stage, organizer, member = setup_case()
    finalize_once(project, stage, member)
    client = cookie_client(Session.issue(organizer).token)
    endpoint = url(workspace, event, project, stage, "reopen/")
    assert (
        client.post(endpoint, {"reason": ["invalid"]}, content_type="application/json").status_code
        == 400
    )
    assert (
        client.post(endpoint, {"reason": "x" * 1001}, content_type="application/json").status_code
        == 400
    )
    assert (
        client.post(
            endpoint, {"reason": "broken link"}, content_type="application/json"
        ).status_code
        == 200
    )
    assert AuditEvent.objects.get(action="submission.reopened").metadata["reason"] == "broken link"


def test_diff_endpoint_reports_the_change_between_the_two_versions():
    workspace, event, project, stage, organizer, member = setup_case()
    finalize_once(project, stage, member, notes="First")
    reopen_submission(project, stage, organizer)
    save_draft(project, stage, member, payload={"notes": "Second", "artifact_ids": []}, revision=1)
    finalize_submission(project, stage, member, revision=2)

    client = cookie_client(Session.issue(organizer).token)
    response = client.get(url(workspace, event, project, stage, "diff/"))
    assert response.status_code == 200
    body = response.json()
    assert body["from_version"] == 1
    assert body["to_version"] == 2
    assert body["diff"]["draft"]["changed"]["notes"] == {"before": "First", "after": "Second"}


def test_diff_endpoint_requires_at_least_two_versions():
    workspace, event, project, stage, organizer, member = setup_case()
    finalize_once(project, stage, member)
    client = cookie_client(Session.issue(organizer).token)
    response = client.get(url(workspace, event, project, stage, "diff/"))
    assert response.status_code == 400


def test_diff_endpoint_rejects_invalid_and_reversed_version_numbers():
    workspace, event, project, stage, organizer, member = setup_case()
    finalize_once(project, stage, member)
    reopen_submission(project, stage, organizer)
    save_draft(project, stage, member, payload={"notes": "Second", "artifact_ids": []}, revision=1)
    finalize_submission(project, stage, member, revision=2)
    client = cookie_client(Session.issue(organizer).token)
    endpoint = url(workspace, event, project, stage, "diff/")
    assert client.get(endpoint + "?from=unknown").status_code == 400
    assert client.get(endpoint + "?from=3").status_code == 400
    assert client.get(endpoint + "?from=2&to=1").status_code == 400
    assert client.get(endpoint + "?to=1").status_code == 400


def test_reopen_and_diff_endpoints_are_organizer_only():
    workspace, event, project, stage, organizer, member = setup_case()
    finalize_once(project, stage, member)
    member_client = cookie_client(Session.issue(member).token)
    assert member_client.post(url(workspace, event, project, stage, "reopen/")).status_code == 403
    assert member_client.get(url(workspace, event, project, stage, "diff/")).status_code == 403
