from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactKind, ArtifactStatus, ArtifactVisibility
from awards.models import Award
from community.models import AbuseSignal, AbuseSignalType, VotingPlan
from django.test import Client
from django.utils import timezone
from evaluations.models import EvaluationPlan, RubricVersion
from events.models import Event, EventStatus
from forms.models import FormDefinition
from participation.models import Team, TeamMembership
from presentation.models import Page, PageBlock
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="ops-organizer", password="unused")
    unteamed = User.objects.create_user(username="ops-unteamed", password="unused")
    teamed = User.objects.create_user(username="ops-teamed", password="unused")
    workspace = Workspace.objects.create(name="Ops", slug="ops")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=unteamed, workspace=workspace, role=Role.PARTICIPANT)
    Membership.objects.create(user=teamed, workspace=workspace, role=Role.PARTICIPANT)
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="Ops Event",
        slug="ops-event",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        status=EventStatus.OPEN,
        is_public=True,
    )

    complete_team = Team.objects.create(event=event, name="Complete")
    TeamMembership.objects.create(team=complete_team, user=teamed)
    project = Project.objects.create(
        event=event, team=complete_team, created_by=teamed, name="Complete project"
    )
    Artifact.objects.create(
        project=project,
        kind=ArtifactKind.LIVE_URL,
        visibility=ArtifactVisibility.PUBLIC,
        title="Demo",
        external_url="https://example.com",
        status=ArtifactStatus.READY,
        created_by=teamed,
    )

    blocked_team = Team.objects.create(event=event, name="Blocked")

    stage = Stage.objects.create(event=event, name="Finals")
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    RubricVersion.objects.create(
        plan=plan,
        number=1,
        criteria=[{"id": "c1", "name": "C1", "weight": 1, "min_score": 0, "max_score": 10}],
    )

    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="hero", config={"headline": "Welcome"})

    Award.objects.create(event=event, name="Best in show")

    voting_plan = VotingPlan.objects.create(
        event=event, opens_at=now - timedelta(hours=1), closes_at=now + timedelta(hours=1)
    )
    AbuseSignal.objects.create(
        plan=voting_plan,
        signal_type=AbuseSignalType.RATE_LIMIT_EXCEEDED,
        detail="Too many attempts.",
    )

    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    return workspace, event, client, project, blocked_team, unteamed


def base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/operations/"


def test_summary_surfaces_blockers_across_domains():
    workspace, event, client, project, blocked_team, unteamed = fixture()
    assert Client().get(base(workspace, event) + "summary/").status_code in (401, 403)
    response = client.get(base(workspace, event) + "summary/")
    assert response.status_code == 200
    body = response.json()

    participants = body["participants"]
    assert participants["participant_count"] == 2
    assert unteamed.username in participants["unteamed"]["items"]
    assert blocked_team.name in participants["teams_without_project"]["items"]

    submissions = body["submissions"]
    assert submissions["project_count"] == 1
    assert submissions["counts"]["ready"] == 1

    judging = body["judging"]
    assert judging["plans"][0]["name"] == "Judging"
    assert judging["plans"][0]["rubric_published"] is True

    stages = body["stages"]
    assert stages["stages"][0]["name"] == "Finals"
    assert stages["stages"][0]["active_entries"] == 0

    publication = body["publication"]
    assert publication["event_public"] is True
    assert publication["page_configured"] is True
    assert publication["page_block_count"] == 1
    assert publication["award_count"] == 1
    assert publication["awards_published"] == 0

    moderation = body["moderation"]
    assert moderation["voting_configured"] is True
    assert moderation["unresolved_signals"]["total"] == 1


def test_summary_flags_missing_artifacts_and_blocked_preflight():
    workspace, event, client, project, blocked_team, unteamed = fixture()
    second = Project.objects.create(
        event=event, team=blocked_team, created_by=unteamed, name="Bare"
    )
    FormDefinition.objects.create(
        event=event, name="Submission", draft_schema={}
    )  # unpublished form => blocked preflight for every project
    response = client.get(base(workspace, event) + "summary/")
    body = response.json()
    assert second.name in body["submissions"]["missing_artifacts"]["items"]
    assert body["submissions"]["counts"]["blocked"] == 2
    assert body["submissions"]["blocked_projects"]["total"] == 2
