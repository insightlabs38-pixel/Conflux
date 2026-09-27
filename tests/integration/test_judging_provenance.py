import pytest
from accounts.models import Session, User
from awards.models import Award, AwardWinner, SelectionSource
from django.test import Client
from evaluations.models import EvaluationPlan, NormalizationRun
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10},
    {"id": "craft", "name": "Craft", "weight": 3, "min_score": 0, "max_score": 10},
]


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def post_json(client, url, data):
    return client.post(url, data=data, content_type="application/json")


def fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judges = [User.objects.create_user(username=f"judge{i}", password="unused") for i in range(2)]
    workspace = Workspace.objects.create(name="Provenance", slug="provenance")
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
    plan = EvaluationPlan.objects.create(stage=stage, name="Final", draft_criteria=CRITERIA)
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/"
    )
    return event, plan, organizer, judges, projects, url


def submit(client, url, project, impact, craft):
    response = post_json(
        client,
        url + "ballots/",
        {
            "project": str(project.public_id),
            "responses": [
                {"criterion_id": "impact", "score": impact},
                {"criterion_id": "craft", "score": craft},
            ],
        },
    )
    assert response.status_code == 201, response.content
    return response.json()


def test_provenance_traces_frozen_ballots_to_published_result_and_award():
    event, plan, organizer, judges, projects, url = fixture()
    owner = client_for(organizer)
    assert owner.post(url + "publish-rubric/").status_code == 201
    authored = submit(client_for(judges[0]), url, projects[0], 2, 8)
    submit(client_for(judges[1]), url, projects[0], 8, 8)
    run_response = post_json(owner, url + "normalization-runs/", {})
    assert run_response.status_code == 201
    run = run_response.json()
    assert (
        post_json(
            owner, url + "publish-results/", {"normalization_run": run["public_id"]}
        ).status_code
        == 200
    )

    award = Award.objects.create(
        event=event,
        name="Best Project",
        selection_source=SelectionSource.EVALUATION,
        evaluation_plan=plan,
    )
    winner = AwardWinner.objects.create(
        award=award,
        project=projects[0],
        selected_by=organizer,
        source=SelectionSource.EVALUATION,
        evidence={"normalization_run": run["public_id"], "rank": 1},
    )
    submit(client_for(judges[0]), url, projects[1], 10, 10)

    response = owner.get(url + f"provenance/{projects[0].public_id}/")
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["normalization_run"] == run["public_id"]
    assert body["ballot_snapshot_available"] is True
    assert body["rank"] == 1
    assert body["raw_score"] == pytest.approx(7.25)
    assert body["final_score"] == pytest.approx(
        run["evidence"]["projects"][str(projects[0].id)]["final"]
    )
    assert len(body["ballots"]) == 2
    first = next(b for b in body["ballots"] if b["ballot"] == authored["public_id"])
    assert first["judge"] == str(judges[0].public_id)
    assert first["weighted_score"] == pytest.approx(6.5)
    assert first["adjusted_score"] == pytest.approx(first["weighted_score"] - first["judge_effect"])
    assert first["responses"] == [
        {"criterion_id": "impact", "criterion_name": "Impact", "weight": 1, "score": 2.0},
        {"criterion_id": "craft", "criterion_name": "Craft", "weight": 3, "score": 8.0},
    ]
    assert body["awards"] == [
        {
            "award": str(award.public_id),
            "name": award.name,
            "winner": str(winner.public_id),
            "rank_at_selection": 1,
            "override_reason": "",
            "published": False,
        }
    ]
    assert len(run["evidence"]["ballots"]) == 2


def test_provenance_fails_closed_for_unpublished_unscored_and_nonorganizer():
    _, plan, organizer, judges, projects, url = fixture()
    owner = client_for(organizer)
    path = url + f"provenance/{projects[0].public_id}/"
    assert owner.get(path).status_code == 404
    assert client_for(judges[0]).get(path).status_code == 403
    assert Client().get(path).status_code in (401, 403)
    assert owner.post(url + "publish-rubric/").status_code == 201
    submit(client_for(judges[0]), url, projects[0], 2, 8)
    run = post_json(owner, url + "normalization-runs/", {}).json()
    assert (
        post_json(
            owner, url + "publish-results/", {"normalization_run": run["public_id"]}
        ).status_code
        == 200
    )
    assert owner.get(url + f"provenance/{projects[1].public_id}/").status_code == 404
    assert plan.normalization_runs.count() == 1


def test_older_run_without_ballot_snapshot_is_explicitly_unavailable():
    event, plan, organizer, judges, projects, url = fixture()
    owner = client_for(organizer)
    owner.post(url + "publish-rubric/")
    submit(client_for(judges[0]), url, projects[0], 2, 8)
    first = post_json(owner, url + "normalization-runs/", {}).json()
    evidence = {key: value for key, value in first["evidence"].items() if key != "ballots"}
    old = NormalizationRun.objects.create(
        plan=plan,
        number=2,
        ridge_lambda=1,
        iterations=first["iterations"],
        converged=first["converged"],
        grand_mean=first["grand_mean"],
        evidence=evidence,
    )
    assert (
        post_json(
            owner, url + "publish-results/", {"normalization_run": str(old.public_id)}
        ).status_code
        == 200
    )
    award = Award.objects.create(
        event=event,
        name="Earlier decision",
        selection_source=SelectionSource.EVALUATION,
        evaluation_plan=plan,
    )
    AwardWinner.objects.create(
        award=award,
        project=projects[0],
        selected_by=organizer,
        source=SelectionSource.EVALUATION,
        evidence={"normalization_run": first["public_id"], "rank": 1},
    )
    body = owner.get(url + f"provenance/{projects[0].public_id}/").json()
    assert body["ballot_snapshot_available"] is False
    assert body["ballots"] is None
    assert body["awards"] == []
