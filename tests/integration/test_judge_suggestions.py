import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    JudgeExpertiseProfile,
    PoolMembership,
    RubricVersion,
)
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def suggest_url(workspace, event, pool):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/evaluation-pools/{pool.public_id}/suggest-judges/"
    )


def fixture():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    judge_a = User.objects.create_user(username="judge_a")  # relevant + reliable
    judge_b = User.objects.create_user(username="judge_b")  # no expertise, dropped the ball
    judge_c = User.objects.create_user(username="judge_c")  # relevant, no history yet
    judge_d = User.objects.create_user(username="judge_d")  # no expertise, no history
    judge_member = User.objects.create_user(username="judge_member")  # already in target pool
    outsider = User.objects.create_user(username="outsider")
    for judge in (judge_a, judge_b, judge_c, judge_d, judge_member):
        Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)

    JudgeExpertiseProfile.objects.create(workspace=workspace, judge=judge_a, tags=["ai"])
    JudgeExpertiseProfile.objects.create(workspace=workspace, judge=judge_c, tags=["ai"])

    past_event = Event.objects.create(workspace=workspace, name="Past event", slug="past")
    past_stage = Stage.objects.create(event=past_event, name="Final")
    Track.objects.create(event=past_event, name="AI")
    past_pool = EvaluationPool.objects.create(event=past_event, name="Panel")
    PoolMembership.objects.create(pool=past_pool, judge=judge_a)
    PoolMembership.objects.create(pool=past_pool, judge=judge_b)
    past_projects = [
        Project.objects.create(event=past_event, name=f"Entry {i}", created_by=organizer)
        for i in range(2)
    ]
    for project in past_projects:
        Submission.objects.create(project=project, stage=past_stage, updated_by=organizer)
    past_plan = EvaluationPlan.objects.create(
        stage=past_stage,
        name="Panel",
        pool=past_pool,
        pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET,
        draft_criteria=CRITERIA,
    )
    version = AssignmentVersion.objects.create(plan=past_plan, number=1, coverage=2)
    Assignment.objects.bulk_create(
        Assignment(version=version, judge=judge, project=project)
        for judge in (judge_a, judge_b)
        for project in past_projects
    )
    past_plan.active_assignment_version = version
    past_plan.save(update_fields=["active_assignment_version"])
    rubric = RubricVersion.objects.create(plan=past_plan, number=1, criteria=CRITERIA)
    for project in past_projects:
        Ballot.objects.create(rubric_version=rubric, judge=judge_a, project=project)
    # judge_b never submitted -- assigned but zero completed ballots.

    event = Event.objects.create(workspace=workspace, name="Current event", slug="current")
    Stage.objects.create(event=event, name="Final")
    Track.objects.create(event=event, name="Ai")  # case-insensitive match against "ai"
    pool = EvaluationPool.objects.create(event=event, name="Panel")
    PoolMembership.objects.create(pool=pool, judge=judge_member)

    return (
        workspace,
        event,
        pool,
        organizer,
        judge_a,
        judge_b,
        judge_c,
        judge_d,
        judge_member,
        outsider,
    )


def test_suggestions_rank_by_track_match_then_reliability_and_exclude_pool_members():
    workspace, event, pool, organizer, judge_a, judge_b, judge_c, judge_d, judge_member, _ = (
        fixture()
    )
    response = client(organizer).get(suggest_url(workspace, event, pool))
    assert response.status_code == 200
    body = response.json()
    usernames = [row["username"] for row in body]
    assert usernames == ["judge_a", "judge_c", "judge_b", "judge_d"]
    assert all(row["judge"] != str(judge_member.public_id) for row in body)

    by_username = {row["username"]: row for row in body}
    a = by_username["judge_a"]
    assert a["matched_tags"] == ["ai"]
    assert a["ballots_completed"] == 2
    assert a["assignments_received"] == 2
    assert a["completion_rate"] == 1.0
    assert a["events_judged"] == 1

    b = by_username["judge_b"]
    assert b["matched_tags"] == []
    assert b["ballots_completed"] == 0
    assert b["assignments_received"] == 2
    assert b["completion_rate"] == 0.0

    c = by_username["judge_c"]
    assert c["matched_tags"] == ["ai"]
    assert c["assignments_received"] == 0
    assert c["completion_rate"] is None

    d = by_username["judge_d"]
    assert d["matched_tags"] == []
    assert d["assignments_received"] == 0
    assert d["completion_rate"] is None

    assert [row["rank"] for row in body] == [1, 2, 3, 4]


def test_suggestions_require_organizer_role():
    workspace, event, pool, organizer, judge_a, _, _, _, _, outsider = fixture()
    url = suggest_url(workspace, event, pool)
    assert client(judge_a).get(url).status_code == 403
    assert client(outsider).get(url).status_code == 403
