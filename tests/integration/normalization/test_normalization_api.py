import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import Ballot, EvaluationPlan, RubricVersion
from evaluations.scoring import ballot_observations
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


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    harsh = User.objects.create_user(username="harsh", password="unused")
    lenient = User.objects.create_user(username="lenient", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=harsh, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=lenient, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(2):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Judge panel", draft_criteria=CRITERIA)
    return workspace, event, stage, plan, organizer, harsh, lenient, projects


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
    return response


def test_normalization_run_estimates_bias_from_real_ballots_and_persists_evidence():
    workspace, event, stage, plan, organizer, harsh, lenient, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(plan_url(workspace, event, stage, plan, "publish-rubric/"))

    harsh_client = cookie_client(Session.issue(harsh).token)
    lenient_client = cookie_client(Session.issue(lenient).token)
    ballots_url = plan_url(workspace, event, stage, plan, "ballots/")
    cast_ballot(harsh_client, ballots_url, projects[0], 2)
    cast_ballot(harsh_client, ballots_url, projects[1], 3)
    cast_ballot(lenient_client, ballots_url, projects[0], 8)
    cast_ballot(lenient_client, ballots_url, projects[1], 9)

    runs_url = plan_url(workspace, event, stage, plan, "normalization-runs/")
    created = organizer_client.post(
        runs_url, data={"ridge_lambda": 0}, content_type="application/json"
    )
    assert created.status_code == 201
    body = created.json()
    assert body["number"] == 1
    assert body["converged"] is True
    judge_effects = body["evidence"]["judge_effects"]
    assert judge_effects[str(harsh.id)] < 0 < judge_effects[str(lenient.id)]
    assert set(body["evidence"]["projects"]) == {str(p.id) for p in projects}

    listed = organizer_client.get(runs_url).json()
    assert len(listed) == 1

    again = organizer_client.post(runs_url, data={}, content_type="application/json")
    assert again.json()["number"] == 2


def test_normalization_endpoint_is_organizer_only():
    workspace, event, stage, plan, organizer, harsh, _, _ = make_fixture()
    runs_url = plan_url(workspace, event, stage, plan, "normalization-runs/")
    judge_client = cookie_client(Session.issue(harsh).token)
    assert judge_client.get(runs_url).status_code == 403
    assert judge_client.post(runs_url, data={}, content_type="application/json").status_code == 403


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_ridge_lambda_cannot_create_a_run(value):
    workspace, event, stage, plan, organizer, _, _, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    response = client.post(
        plan_url(workspace, event, stage, plan, "normalization-runs/"),
        data={"ridge_lambda": value},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert plan.normalization_runs.count() == 0


def test_ballot_observations_use_each_ballots_own_frozen_rubric_weights():
    # NORM-002: republishing the rubric with different weights must never
    # change what an already-cast ballot's aggregate score means.
    workspace, event, stage, plan, organizer, harsh, _, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(plan_url(workspace, event, stage, plan, "publish-rubric/"))

    harsh_client = cookie_client(Session.issue(harsh).token)
    cast_ballot(harsh_client, plan_url(workspace, event, stage, plan, "ballots/"), projects[0], 4)

    ballot = Ballot.objects.get(judge=harsh, project=projects[0])
    original_version = ballot.rubric_version
    assert original_version.number == 1

    # Republish with a second, differently-weighted criterion set.
    plan.draft_criteria = [
        {"id": "impact", "name": "Impact", "weight": 5, "min_score": 0, "max_score": 10},
    ]
    plan.save()
    organizer_client.post(plan_url(workspace, event, stage, plan, "publish-rubric/"))
    assert RubricVersion.objects.filter(plan=plan).count() == 2

    observations = ballot_observations(plan)
    assert observations == [(harsh.id, projects[0].id, 4.0)]
    ballot.refresh_from_db()
    assert ballot.rubric_version_id == original_version.id  # untouched by republishing
