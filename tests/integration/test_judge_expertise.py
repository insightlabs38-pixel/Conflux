import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.assignment import compute_assignment
from evaluations.models import (
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    JudgeExpertiseProfile,
    PoolMembership,
)
from evaluations.optimization import compute_assignment_optimized
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def profile_url(workspace, suffix="my-judge-expertise/"):
    return f"/api/v1/workspaces/{workspace.public_id}/{suffix}"


def fixture():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    first = User.objects.create_user(username="first")
    expert = User.objects.create_user(username="expert")
    outsider = User.objects.create_user(username="outsider")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=first, role=Role.JUDGE)
    Membership.objects.create(workspace=workspace, user=expert, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="First event", slug="first")
    stage = Stage.objects.create(event=event, name="Final")
    track = Track.objects.create(event=event, name="AI")
    pool = EvaluationPool.objects.create(event=event, name="Panel")
    PoolMembership.objects.create(pool=pool, judge=first)
    PoolMembership.objects.create(pool=pool, judge=expert)
    project = Project.objects.create(event=event, name="Entry", track=track, created_by=organizer)
    Submission.objects.create(project=project, stage=stage, updated_by=organizer)
    plan = EvaluationPlan.objects.create(
        stage=stage,
        name="Panel",
        pool=pool,
        pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET,
    )
    return workspace, organizer, first, expert, outsider, event, track, plan, project


def test_profile_is_private_to_workspace_and_normalized():
    workspace, organizer, first, expert, outsider, _, _, _, _ = fixture()
    expert_client = client(expert)
    own = profile_url(workspace)
    assert expert_client.get(own).json()["tags"] == []
    response = expert_client.put(
        own, {"tags": [" AI ", "Data Science"]}, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["tags"] == ["ai", "data science"]
    target = profile_url(workspace, f"judge-expertise/{expert.public_id}/")
    assert client(organizer).get(target).json()["tags"] == ["ai", "data science"]
    assert client(first).get(target).status_code == 403
    assert client(outsider).get(target).status_code == 403
    assert (
        expert_client.put(own, {"tags": ["AI", "ai"]}, content_type="application/json").status_code
        == 400
    )
    assert (
        expert_client.put(own, {"tags": ["a"] * 21}, content_type="application/json").status_code
        == 400
    )
    assert JudgeExpertiseProfile.objects.get(workspace=workspace, judge=expert).tags == [
        "ai",
        "data science",
    ]


def test_profile_tags_feed_both_assignment_solvers_and_reuse_across_events():
    workspace, organizer, first, expert, _, _, _, plan, project = fixture()
    expert_client = client(expert)
    assert (
        expert_client.put(
            profile_url(workspace), {"tags": ["ai"]}, content_type="application/json"
        ).status_code
        == 200
    )
    assert [
        (pairing.judge_id, pairing.project_id) for pairing in compute_assignment(plan, coverage=1)
    ] == [(expert.id, project.id)]
    assert [
        (pairing.judge_id, pairing.project_id)
        for pairing in compute_assignment_optimized(plan, coverage=1)
    ] == [(expert.id, project.id)]

    second_event = Event.objects.create(workspace=workspace, name="Second event", slug="second")
    second_stage = Stage.objects.create(event=second_event, name="Final")
    second_track = Track.objects.create(event=second_event, name="Ai")
    second_pool = EvaluationPool.objects.create(event=second_event, name="Panel")
    PoolMembership.objects.create(pool=second_pool, judge=first)
    PoolMembership.objects.create(pool=second_pool, judge=expert)
    second_project = Project.objects.create(
        event=second_event, name="Entry", track=second_track, created_by=organizer
    )
    Submission.objects.create(project=second_project, stage=second_stage, updated_by=organizer)
    second_plan = EvaluationPlan.objects.create(
        stage=second_stage,
        name="Panel",
        pool=second_pool,
        pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET,
    )
    assert [pairing.judge_id for pairing in compute_assignment(second_plan, coverage=1)] == [
        expert.id
    ]

    assert (
        expert_client.put(
            profile_url(workspace), {"tags": []}, content_type="application/json"
        ).status_code
        == 200
    )
    assert [pairing.judge_id for pairing in compute_assignment(plan, coverage=1)] == [first.id]
