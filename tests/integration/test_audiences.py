import pytest
from accounts.models import Session, User
from communications.audiences import resolve_audience
from django.core.exceptions import ValidationError
from django.test import Client
from evaluations.models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    EvaluationPlan,
    EvaluationPoolStrategy,
    RubricVersion,
)
from events.models import Event, Track
from participation.models import Team, TeamMembership
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="aud-organizer", password="unused")
    participant_a = User.objects.create_user(username="aud-participant-a", password="unused")
    participant_b = User.objects.create_user(username="aud-participant-b", password="unused")
    judge = User.objects.create_user(username="aud-judge", password="unused")
    workspace = Workspace.objects.create(name="Audiences", slug="audiences")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=participant_a, workspace=workspace, role=Role.PARTICIPANT)
    Membership.objects.create(user=participant_b, workspace=workspace, role=Role.PARTICIPANT)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    track = Track.objects.create(event=event, name="Hardware")

    teamed_team = Team.objects.create(event=event, name="Teamed")
    TeamMembership.objects.create(team=teamed_team, user=participant_a)
    project = Project.objects.create(
        event=event, team=teamed_team, track=track, created_by=participant_a, name="Project"
    )
    blocked_team = Team.objects.create(event=event, name="Blocked")

    return {
        "workspace": workspace,
        "event": event,
        "track": track,
        "organizer": organizer,
        "participant_a": participant_a,
        "participant_b": participant_b,
        "judge": judge,
        "project": project,
        "blocked_team": blocked_team,
    }


def test_static_role_audiences():
    ctx = fixture()
    event = ctx["event"]
    assert set(resolve_audience(event, "all_participants")) == {
        ctx["participant_a"],
        ctx["participant_b"],
    }
    assert set(resolve_audience(event, "all_judges")) == {ctx["judge"]}
    assert set(resolve_audience(event, "all_organizers")) == {ctx["organizer"]}


def test_unteamed_and_blocked_teams():
    ctx = fixture()
    event = ctx["event"]
    assert set(resolve_audience(event, "unteamed_participants")) == {ctx["participant_b"]}
    assert set(resolve_audience(event, "teams_without_project")) == set()
    TeamMembership.objects.create(team=ctx["blocked_team"], user=ctx["participant_b"])
    assert set(resolve_audience(event, "teams_without_project")) == {ctx["participant_b"]}


def test_track_participants_requires_a_valid_track():
    ctx = fixture()
    event = ctx["event"]
    with pytest.raises(ValidationError):
        resolve_audience(event, "track_participants", {})
    assert set(
        resolve_audience(event, "track_participants", {"track": str(ctx["track"].public_id)})
    ) == {ctx["participant_a"]}


def test_judges_with_incomplete_assignments():
    ctx = fixture()
    event = ctx["event"]
    other_judge = User.objects.create_user(username="aud-judge-2", password="unused")
    Membership.objects.create(user=other_judge, workspace=ctx["workspace"], role=Role.JUDGE)
    stage = Stage.objects.create(event=event, name="Finals")
    plan = EvaluationPlan.objects.create(
        stage=stage, name="Judging", pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET
    )
    rubric = RubricVersion.objects.create(
        plan=plan,
        number=1,
        criteria=[{"id": "c1", "name": "C1", "weight": 1, "min_score": 0, "max_score": 10}],
    )
    version = AssignmentVersion.objects.create(plan=plan, number=1, coverage=1, evidence={})
    plan.active_assignment_version = version
    plan.save(update_fields=["active_assignment_version"])
    Assignment.objects.create(version=version, judge=ctx["judge"], project=ctx["project"])
    Assignment.objects.create(version=version, judge=other_judge, project=ctx["project"])
    Ballot.objects.create(rubric_version=rubric, judge=ctx["judge"], project=ctx["project"])

    with pytest.raises(ValidationError):
        resolve_audience(event, "judges_incomplete_assignments", {})
    incomplete = resolve_audience(
        event, "judges_incomplete_assignments", {"plan": str(plan.public_id)}
    )
    assert set(incomplete) == {other_judge}


def test_unassigned_ballot_does_not_hide_a_missing_active_assignment():
    ctx = fixture()
    event = ctx["event"]
    stage = Stage.objects.create(event=event, name="Finals")
    plan = EvaluationPlan.objects.create(
        stage=stage, name="Judging", pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET
    )
    rubric = RubricVersion.objects.create(
        plan=plan,
        number=1,
        criteria=[{"id": "c1", "name": "C1", "weight": 1, "min_score": 0, "max_score": 10}],
    )
    version = AssignmentVersion.objects.create(plan=plan, number=1, coverage=1, evidence={})
    plan.active_assignment_version = version
    plan.save(update_fields=["active_assignment_version"])
    assigned = ctx["project"]
    other = Project.objects.create(event=event, created_by=ctx["participant_b"], name="Other")
    Assignment.objects.create(version=version, judge=ctx["judge"], project=assigned)
    Ballot.objects.create(rubric_version=rubric, judge=ctx["judge"], project=other)
    params = {"plan": str(plan.public_id)}
    assert set(resolve_audience(event, "judges_incomplete_assignments", params)) == {ctx["judge"]}
    Ballot.objects.create(rubric_version=rubric, judge=ctx["judge"], project=assigned)
    assert set(resolve_audience(event, "judges_incomplete_assignments", params)) == set()


def test_blocked_team_audience_re_resolves_at_send_time():
    ctx = fixture()
    event = ctx["event"]
    TeamMembership.objects.create(team=ctx["blocked_team"], user=ctx["participant_b"])
    client = Client()
    client.cookies["session"] = Session.issue(ctx["organizer"]).token
    prefix = (
        f"/api/v1/workspaces/{ctx['workspace'].public_id}/events/{event.public_id}/communications/"
    )
    preview = client.post(
        prefix + "audiences/preview/",
        {"audience_kind": "teams_without_project"},
        content_type="application/json",
    )
    assert preview.status_code == 200
    assert preview.json()["count"] == 1
    Project.objects.create(
        event=event, team=ctx["blocked_team"], created_by=ctx["participant_b"], name="New"
    )
    sent = client.post(
        prefix + "messages/",
        {"subject": "Check", "body": "Please review", "audience_kind": "teams_without_project"},
        content_type="application/json",
    )
    assert sent.status_code == 201
    assert sent.json()["recipient_count"] == 0


def test_audience_endpoints_list_and_preview():
    ctx = fixture()
    workspace, event = ctx["workspace"], ctx["event"]
    client = Client()
    client.cookies["session"] = Session.issue(ctx["organizer"]).token
    prefix = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/communications/"

    kinds = client.get(prefix + "audiences/").json()
    keys = {row["key"] for row in kinds}
    assert "unteamed_participants" in keys
    track_kind = next(row for row in kinds if row["key"] == "track_participants")
    assert track_kind["options"]["track"][0]["label"] == "Hardware"

    preview = client.post(
        prefix + "audiences/preview/",
        {"audience_kind": "all_participants"},
        content_type="application/json",
    )
    assert preview.status_code == 200
    assert preview.json()["count"] == 2
