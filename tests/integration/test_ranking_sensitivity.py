import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import Ballot, EvaluationMode, EvaluationPlan, NormalizationRun
from evaluations.scoring import ballot_observations
from evaluations.sensitivity import chronological_observations
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judges = [User.objects.create_user(username=f"judge{i}", password="unused") for i in range(2)]
    workspace = Workspace.objects.create(name="Sensitivity", slug="sensitivity")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    for judge in judges:
        Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(2):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Rubric", draft_criteria=CRITERIA)
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/"
    )
    return plan, organizer, judges, projects, url


def post_json(client, url, data):
    return client.post(url, data=data, content_type="application/json")


def submit(client, url, project, score):
    response = post_json(
        client,
        url + "ballots/",
        {
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": score}],
        },
    )
    assert response.status_code == 201, response.content


def test_sensitivity_uses_current_ballots_and_never_creates_runs():
    plan, organizer, judges, projects, url = fixture()
    owner = client_for(organizer)
    assert owner.post(url + "publish-rubric/").status_code == 201
    j0, j1 = [client_for(j) for j in judges]
    p0, p1 = projects
    submit(j0, url, p0, 9)
    submit(j0, url, p1, 1)
    submit(j1, url, p0, 1)
    submit(j1, url, p1, 8)

    response = post_json(
        owner, url + "sensitivity/", {"ridge_lambdas": [0, 1, 5], "holdout_counts": [1, 2, 4]}
    )
    assert response.status_code == 200, response.content
    body = response.json()
    baseline = [str(p.public_id) for p in projects]
    assert body["ridge_lambda"]["baseline"] == baseline
    assert set(body["ridge_lambda"]["scenarios"]) == {"0", "1", "5"}
    assert body["ridge_lambda"]["scenarios"]["1"]["rank_changed"] is False
    removed = body["judge_removal"]["scenarios"]
    assert set(removed) == {j.username for j in judges}
    assert removed["judge0"] == {"order": baseline[::-1], "rank_changed": True}
    assert set(body["incompleteness"]["scenarios"]) == {"1", "2"}
    assert body["incompleteness"]["scenarios"]["2"]["order"] == baseline
    assert NormalizationRun.objects.count() == 0
    assert Ballot.objects.count() == 4
    assert chronological_observations(plan) == ballot_observations(plan)


def test_sensitivity_empty_and_custom_empty_scenarios():
    _, organizer, _, _, url = fixture()
    owner = client_for(organizer)
    response = post_json(owner, url + "sensitivity/", {})
    assert response.status_code == 200
    assert all(block["baseline"] == [] for block in response.json().values())
    assert response.json()["judge_removal"]["scenarios"] == {}
    assert response.json()["incompleteness"]["scenarios"] == {}
    assert all(
        scenario == {"order": [], "rank_changed": False}
        for scenario in response.json()["ridge_lambda"]["scenarios"].values()
    )
    response = post_json(owner, url + "sensitivity/", {"ridge_lambdas": [], "holdout_counts": []})
    assert response.status_code == 200
    assert response.json()["ridge_lambda"]["scenarios"] == {}


@pytest.mark.parametrize(
    "payload",
    [
        {"ridge_lambdas": [-1]},
        {"ridge_lambdas": [True]},
        {"ridge_lambdas": ["1"]},
        {"ridge_lambdas": [float("nan")]},
        {"ridge_lambdas": [float("inf")]},
        {"ridge_lambdas": [10**400]},
        {"ridge_lambdas": list(range(11))},
        {"holdout_counts": [0]},
        {"holdout_counts": [1.5]},
        {"holdout_counts": [True]},
        {"holdout_counts": list(range(1, 12))},
    ],
)
def test_sensitivity_rejects_invalid_parameters(payload):
    _, organizer, _, _, url = fixture()
    response = post_json(client_for(organizer), url + "sensitivity/", payload)
    assert response.status_code == 400


def test_sensitivity_requires_organizer_and_rubric_mode():
    plan, organizer, judges, _, url = fixture()
    assert post_json(client_for(judges[0]), url + "sensitivity/", {}).status_code == 403
    assert post_json(Client(), url + "sensitivity/", {}).status_code in (401, 403)
    plan.mode = EvaluationMode.PAIRWISE
    plan.save(update_fields=["mode"])
    assert post_json(client_for(organizer), url + "sensitivity/", {}).status_code == 400
