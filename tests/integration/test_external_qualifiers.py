import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from integrations.models import ExternalQualifierBinding
from participation.models import Team, TeamMembership
from projects.models import Project
from stages.models import ParticipationMode, Stage, StageEntry
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="extq-organizer", password="unused")
    creator = User.objects.create_user(username="extq-creator", password="unused")
    workspace = Workspace.objects.create(name="ExtQ", slug="extq")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    stage = Stage.objects.create(
        event=event, name="Finals", participation_mode=ParticipationMode.TEAM_FORMATION
    )
    team = Team.objects.create(event=event, name="Qualified Team")
    TeamMembership.objects.create(team=team, user=creator)
    project = Project.objects.create(event=event, team=team, created_by=creator, name="Project")
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    return workspace, event, stage, team, project, client


def url(workspace, event, stage):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/external-qualifiers/"
    )


def test_first_import_binds_external_ref_and_enters_the_stage():
    workspace, event, stage, team, project, client = fixture()
    response = client.post(
        url(workspace, event, stage),
        {"entries": [{"external_ref": "region-1:team-42", "project": str(project.public_id)}]},
        content_type="application/json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["entries"] == [
        {"external_ref": "region-1:team-42", "project": str(project.public_id), "advanced": True}
    ]
    assert body["advanced_count"] == 1
    assert StageEntry.objects.filter(
        stage=stage, subject_type="team", subject_id=str(team.public_id), exited_at__isnull=True
    ).exists()
    assert ExternalQualifierBinding.objects.filter(
        event=event, external_ref="region-1:team-42", project=project
    ).exists()


def test_repeat_import_by_ref_alone_is_idempotent_identity_continuity():
    workspace, event, stage, team, project, client = fixture()
    first = client.post(
        url(workspace, event, stage),
        {"entries": [{"external_ref": "region-1:team-42", "project": str(project.public_id)}]},
        content_type="application/json",
    )
    assert first.status_code == 201

    # The external system only ever knows its own ref on a repeat call --
    # never our internal public_id -- and must still resolve to the exact
    # same project, without creating a second stage entry.
    second = client.post(
        url(workspace, event, stage),
        {"entries": [{"external_ref": "region-1:team-42"}]},
        content_type="application/json",
    )
    assert second.status_code == 201
    body = second.json()
    assert body["entries"] == [
        {"external_ref": "region-1:team-42", "project": str(project.public_id), "advanced": False}
    ]
    assert ExternalQualifierBinding.objects.filter(event=event).count() == 1
    assert (
        StageEntry.objects.filter(
            stage=stage, subject_type="team", subject_id=str(team.public_id)
        ).count()
        == 1
    )


def test_rebinding_an_existing_ref_to_a_different_project_is_rejected():
    workspace, event, stage, team, project, client = fixture()
    client.post(
        url(workspace, event, stage),
        {"entries": [{"external_ref": "region-1:team-42", "project": str(project.public_id)}]},
        content_type="application/json",
    )
    other_team = Team.objects.create(event=event, name="Other Team")
    other_project = Project.objects.create(
        event=event, team=other_team, created_by=project.created_by, name="Other"
    )
    conflicting = client.post(
        url(workspace, event, stage),
        {
            "entries": [
                {"external_ref": "region-1:team-42", "project": str(other_project.public_id)}
            ]
        },
        content_type="application/json",
    )
    assert conflicting.status_code == 400


def test_unbound_ref_without_a_project_is_rejected():
    workspace, event, stage, _team, _project, client = fixture()
    response = client.post(
        url(workspace, event, stage),
        {"entries": [{"external_ref": "unknown-ref"}]},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_individual_mode_stage_is_rejected():
    workspace, event, _stage, _team, project, client = fixture()
    individual_stage = Stage.objects.create(
        event=event, name="Solo Round", participation_mode=ParticipationMode.INDIVIDUAL
    )
    response = client.post(
        url(workspace, event, individual_stage),
        {"entries": [{"external_ref": "x", "project": str(project.public_id)}]},
        content_type="application/json",
    )
    assert response.status_code == 400
