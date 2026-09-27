import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.assignment import activate, preview
from evaluations.models import (
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    PoolMembership,
)
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture(judge_count=3, project_count=2):
    organizer = User.objects.create_user(username="organizer", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    pool = EvaluationPool.objects.create(event=event, name="Main pool")
    judges = []
    for i in range(judge_count):
        judge = User.objects.create_user(username=f"judge{i}", password="unused")
        Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
        PoolMembership.objects.create(pool=pool, judge=judge)
        judges.append(judge)
    projects = []
    for i in range(project_count):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(
        stage=stage,
        name="Judge panel",
        pool=pool,
        pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET,
        draft_criteria=CRITERIA,
    )
    return workspace, event, stage, plan, organizer, judges, projects


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def test_preview_matches_what_activate_would_freeze_without_writing_anything():
    _, event, stage, plan, organizer, judges, projects = make_fixture()
    previewed = preview(plan, coverage=2)
    assert plan.assignment_versions.count() == 0
    assert plan.active_assignment_version_id is None

    version = activate(plan, coverage=2)
    assert previewed["candidate_count"] == version.evidence["candidate_count"]
    assert previewed["assignment_count"] == version.evidence["assignment_count"]
    assert previewed["load_by_judge"] == version.evidence["load_by_judge"]
    assert previewed["connectivity"] == version.evidence["connectivity"]
    assert previewed["coverage"] == 2


def test_preview_raises_for_a_plan_without_a_pool():
    _, event, stage, plan, organizer, judges, projects = make_fixture()
    plan.pool = None
    plan.save(update_fields=["pool"])
    with pytest.raises(ValueError):
        preview(plan, coverage=1)


def test_preview_endpoint_compares_multiple_coverage_values_and_writes_nothing():
    workspace, event, stage, plan, organizer, judges, projects = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    response = client.post(
        url(workspace, event, stage, plan, "assignments/preview/"),
        data={"coverage_options": [1, 2, 3]},
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    assert [entry["coverage"] for entry in body] == [1, 2, 3]
    assert body[0]["assignment_count"] < body[2]["assignment_count"]
    plan.refresh_from_db()
    assert plan.active_assignment_version_id is None
    assert plan.assignment_versions.count() == 0


def test_preview_endpoint_defaults_to_coverage_three_and_rejects_bad_input():
    workspace, event, stage, plan, organizer, judges, projects = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    default_response = client.post(
        url(workspace, event, stage, plan, "assignments/preview/"),
        data={},
        content_type="application/json",
    )
    assert default_response.status_code == 200
    assert default_response.json()[0]["coverage"] == 3

    bad = client.post(
        url(workspace, event, stage, plan, "assignments/preview/"),
        data={"coverage_options": [0]},
        content_type="application/json",
    )
    assert bad.status_code == 400


def test_preview_endpoint_is_organizer_only():
    workspace, event, stage, plan, organizer, judges, projects = make_fixture()
    client = cookie_client(Session.issue(judges[0]).token)
    response = client.post(
        url(workspace, event, stage, plan, "assignments/preview/"),
        data={},
        content_type="application/json",
    )
    assert response.status_code == 403
