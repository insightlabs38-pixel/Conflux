import pytest
from accounts.models import Session, User
from django.core.exceptions import ValidationError as ModelValidationError
from django.test import Client
from evaluations.hybrid import close_call_project_ids
from evaluations.models import EvaluationMode, EvaluationPlan
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


def make_fixture(project_count=4):
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(project_count):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Screening", draft_criteria=CRITERIA)
    return workspace, event, stage, plan, organizer, judge, projects


def plan_url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def cast_ballot(client, url, project, score):
    response = client.post(
        url,
        data={
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": score}],
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content


def run_screening(organizer_client, judge_client, workspace, event, stage, plan, projects, scores):
    organizer_client.post(plan_url(workspace, event, stage, plan, "publish-rubric/"))
    ballots_url = plan_url(workspace, event, stage, plan, "ballots/")
    for project, score in zip(projects, scores):
        cast_ballot(judge_client, ballots_url, project, score)
    run = organizer_client.post(
        plan_url(workspace, event, stage, plan, "normalization-runs/"),
        data={"ridge_lambda": 0},
        content_type="application/json",
    )
    assert run.status_code == 201
    return run.json()


def make_pairwise_child(stage, source_plan):
    return EvaluationPlan.objects.create(
        stage=stage, name="Tie-break", mode=EvaluationMode.PAIRWISE, hybrid_source=source_plan
    )


def test_close_call_project_ids_groups_the_tight_cluster_and_excludes_the_outlier():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    judge_client = cookie_client(Session.issue(judge).token)
    p0, p1, p2, p3 = projects
    run_screening(
        organizer_client,
        judge_client,
        workspace,
        event,
        stage,
        plan,
        projects,
        [9.0, 8.9, 8.8, 1.0],
    )
    latest_run = plan.normalization_runs.order_by("-number").first()

    close_ids = close_call_project_ids(plan, latest_run)
    assert close_ids == {p0.id, p1.id, p2.id}


def test_close_calls_endpoint_reports_the_same_bounded_set():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    judge_client = cookie_client(Session.issue(judge).token)
    p0, p1, p2, p3 = projects
    run_screening(
        organizer_client,
        judge_client,
        workspace,
        event,
        stage,
        plan,
        projects,
        [9.0, 8.9, 8.8, 1.0],
    )

    body = organizer_client.get(plan_url(workspace, event, stage, plan, "close-calls/")).json()
    assert body["normalization_run"] == 1
    assert set(body["projects"]) == {str(p0.public_id), str(p1.public_id), str(p2.public_id)}


def test_close_calls_endpoint_before_any_run_reports_nothing():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    body = organizer_client.get(plan_url(workspace, event, stage, plan, "close-calls/")).json()
    assert body == {"normalization_run": None, "projects": []}


def test_hybrid_pairwise_plan_bounds_eligibility_to_close_calls_only():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    judge_client = cookie_client(Session.issue(judge).token)
    p0, p1, p2, p3 = projects
    run_screening(
        organizer_client,
        judge_client,
        workspace,
        event,
        stage,
        plan,
        projects,
        [9.0, 8.9, 8.8, 1.0],
    )
    child = make_pairwise_child(stage, plan)

    # Both endpoints inside the close-call cluster: allowed.
    ok = judge_client.post(
        plan_url(workspace, event, stage, child, "pairwise/comparisons/"),
        data={"project_a": str(p0.public_id), "project_b": str(p1.public_id), "winner": None},
        content_type="application/json",
    )
    assert ok.status_code == 201

    # p3 is the clear outlier, never a close call: rejected even though
    # it is a perfectly real, finalized candidate on the same stage.
    blocked = judge_client.post(
        plan_url(workspace, event, stage, child, "pairwise/comparisons/"),
        data={"project_a": str(p0.public_id), "project_b": str(p3.public_id), "winner": None},
        content_type="application/json",
    )
    assert blocked.status_code == 400


def test_hybrid_plan_with_no_published_run_yet_is_bounded_to_nothing():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    judge_client = cookie_client(Session.issue(judge).token)
    child = make_pairwise_child(stage, plan)

    response = judge_client.post(
        plan_url(workspace, event, stage, child, "pairwise/comparisons/"),
        data={
            "project_a": str(projects[0].public_id),
            "project_b": str(projects[1].public_id),
            "winner": None,
        },
        content_type="application/json",
    )
    assert response.status_code == 400


def test_hybrid_source_must_be_a_rubric_plan_on_a_pairwise_plan_on_the_same_stage():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    other_stage = Stage.objects.create(event=event, name="Semis")

    rubric_child = EvaluationPlan(
        stage=stage, name="Bad", mode=EvaluationMode.RUBRIC, hybrid_source=plan
    )
    with pytest.raises(ModelValidationError, match="pairwise plan"):
        rubric_child.full_clean()

    self_referential = EvaluationPlan(stage=stage, name="Self", mode=EvaluationMode.PAIRWISE)
    self_referential.save()
    self_referential.hybrid_source = self_referential
    with pytest.raises(ModelValidationError, match="own hybrid source"):
        self_referential.full_clean()

    pairwise_source = EvaluationPlan.objects.create(
        stage=stage, name="AlsoPairwise", mode=EvaluationMode.PAIRWISE
    )
    wrong_mode = EvaluationPlan(
        stage=stage, name="WrongMode", mode=EvaluationMode.PAIRWISE, hybrid_source=pairwise_source
    )
    with pytest.raises(ModelValidationError, match="rubric plan"):
        wrong_mode.full_clean()

    cross_stage_source = EvaluationPlan.objects.create(
        stage=other_stage, name="OtherStageScreening", draft_criteria=CRITERIA
    )
    wrong_stage = EvaluationPlan(
        stage=stage,
        name="WrongStage",
        mode=EvaluationMode.PAIRWISE,
        hybrid_source=cross_stage_source,
    )
    with pytest.raises(ModelValidationError, match="same stage"):
        wrong_stage.full_clean()


def test_participant_cannot_read_close_calls():
    workspace, event, stage, plan, organizer, judge, projects = make_fixture()
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    client = cookie_client(Session.issue(participant).token)
    assert client.get(plan_url(workspace, event, stage, plan, "close-calls/")).status_code == 403
