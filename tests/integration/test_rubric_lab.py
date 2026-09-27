import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import EvaluationMode, EvaluationPlan, NormalizationRun
from evaluations.rubric_lab import analyze
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [
    {"id": "a", "name": "A", "weight": 1, "min_score": 0, "max_score": 10},
    {"id": "b", "name": "B", "weight": 1, "min_score": 0, "max_score": 10},
]


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def post_json(client, url, data):
    return client.post(url, data=data, content_type="application/json")


def fixture():
    owner = User.objects.create_user(username="owner", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="Rubric lab", slug="rubric-lab")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for index in range(2):
        project = Project.objects.create(event=event, name=f"Project {index}", created_by=owner)
        Submission.objects.create(project=project, stage=stage, updated_by=owner)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging", draft_criteria=CRITERIA)
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/"
    )
    return plan, owner, judge, projects, url


def test_rubric_lab_measures_scale_variance_dominance_and_rank_sensitivity():
    result = analyze(
        CRITERIA,
        [(1, 11, {"a": 10, "b": 0}), (1, 12, {"a": 0, "b": 8})],
        factors=[0.5, 1.5],
    )
    assert result["baseline"] == [11, 12]
    assert result["ballot_count"] == 2
    a, b = result["criteria"]
    assert a["mean"] == 5
    assert a["variance"] == 25
    assert a["scale_use"] == 1
    assert a["at_min_count"] == a["at_max_count"] == 1
    assert a["dominates"] is True
    assert b["dominates"] is False
    assert a["weight_scenarios"][0] == {
        "factor": 0.5,
        "order": [12, 11],
        "rank_changed_count": 2,
        "top_changed": True,
    }
    assert a["weight_scenarios"][1]["top_changed"] is False


def test_rubric_lab_reports_missing_criterion_responses_without_inventing_scores():
    result = analyze(
        CRITERIA,
        [(1, 11, {"a": 8}), (2, 12, {"a": 2, "b": 6})],
        factors=[1],
    )
    a, b = result["criteria"]
    assert a["response_count"] == 2
    assert a["missing_count"] == 0
    assert b["response_count"] == 1
    assert b["missing_count"] == 1
    assert b["variance"] == 0
    assert b["scale_use"] == 0


def test_rubric_lab_uses_selected_historical_version_and_never_writes_runs():
    plan, owner, judge, projects, url = fixture()
    organizer = client_for(owner)
    version = organizer.post(url + "publish-rubric/").json()
    judge_client = client_for(judge)
    for project, a, b in ((projects[0], 10, 0), (projects[1], 0, 8)):
        response = post_json(
            judge_client,
            url + "ballots/",
            {
                "project": str(project.public_id),
                "responses": [
                    {"criterion_id": "a", "score": a},
                    {"criterion_id": "b", "score": b},
                ],
            },
        )
        assert response.status_code == 201, response.content
    plan.draft_criteria = [{**criterion, "weight": 2} for criterion in CRITERIA]
    plan.save(update_fields=["draft_criteria"])
    assert organizer.post(url + "publish-rubric/").status_code == 201

    response = post_json(
        organizer,
        url + "rubric-lab/",
        {"rubric_version": version["public_id"], "factors": [0.5]},
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["rubric_version"] == version["public_id"]
    assert body["ballot_count"] == 2
    assert body["baseline"] == [str(project.public_id) for project in projects]
    assert body["criteria"][0]["weight_scenarios"][0]["order"] == [
        str(project.public_id) for project in reversed(projects)
    ]
    current = post_json(organizer, url + "rubric-lab/", {}).json()
    assert current["ballot_count"] == 0
    assert current["baseline"] == []
    assert current["criteria"][0]["variance"] is None
    assert NormalizationRun.objects.count() == 0


@pytest.mark.parametrize("factors", [[0], [-1], [float("inf")], [float("nan")], [11], [1] * 5])
def test_rubric_lab_rejects_invalid_factors(factors):
    _, owner, _, _, url = fixture()
    assert (
        post_json(client_for(owner), url + "rubric-lab/", {"factors": factors}).status_code == 400
    )


def test_rubric_lab_requires_rubric_version_and_organizer_access():
    plan, owner, judge, projects, url = fixture()
    organizer = client_for(owner)
    assert post_json(organizer, url + "rubric-lab/", {}).status_code == 400
    assert post_json(client_for(judge), url + "rubric-lab/", {}).status_code == 403
    assert (
        post_json(
            organizer, url + "rubric-lab/", {"rubric_version": str(projects[0].public_id)}
        ).status_code
        == 404
    )
    plan.mode = EvaluationMode.PAIRWISE
    plan.save(update_fields=["mode"])
    assert post_json(organizer, url + "rubric-lab/", {}).status_code == 400
