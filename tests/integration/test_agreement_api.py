import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import EvaluationPlan
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10},
]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge_a = User.objects.create_user(username="judge_a", password="unused")
    judge_b = User.objects.create_user(username="judge_b", password="unused")
    participant = User.objects.create_user(username="member", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge_a, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=judge_b, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(3):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", draft_criteria=CRITERIA)
    return workspace, event, stage, plan, organizer, judge_a, judge_b, participant, projects


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def submit_ballot(client, workspace, event, stage, plan, project, score):
    return client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": score}],
        },
        content_type="application/json",
    )


def test_agreement_summary_reports_dispersion_and_rank_correlation():
    workspace, event, stage, plan, organizer, judge_a, judge_b, _, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))

    judge_a_client = cookie_client(Session.issue(judge_a).token)
    judge_b_client = cookie_client(Session.issue(judge_b).token)
    # Both judges rank the three projects identically: p0 > p1 > p2.
    for project, (score_a, score_b) in zip(projects, [(9, 8), (5, 6), (1, 2)], strict=True):
        submit_ballot(judge_a_client, workspace, event, stage, plan, project, score_a)
        submit_ballot(judge_b_client, workspace, event, stage, plan, project, score_b)

    response = organizer_client.get(url(workspace, event, stage, plan, "agreement/"))
    assert response.status_code == 200
    body = response.json()

    assert len(body["criteria"]) == 3
    for entry in body["criteria"]:
        assert entry["criterion_id"] == "impact"
        assert len(entry["scores"]) == 2

    assert len(body["rankings"]) == 1
    ranking = body["rankings"][0]
    assert ranking["shared_candidates"] == 3
    assert ranking["tau"] == 1.0


def test_agreement_summary_reports_null_tau_below_the_minimum_shared_candidates():
    workspace, event, stage, plan, organizer, judge_a, judge_b, _, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))

    judge_a_client = cookie_client(Session.issue(judge_a).token)
    judge_b_client = cookie_client(Session.issue(judge_b).token)
    submit_ballot(judge_a_client, workspace, event, stage, plan, projects[0], 9)
    submit_ballot(judge_b_client, workspace, event, stage, plan, projects[0], 2)

    body = organizer_client.get(url(workspace, event, stage, plan, "agreement/")).json()
    assert body["rankings"][0]["shared_candidates"] == 1
    assert body["rankings"][0]["tau"] is None


def test_agreement_summary_is_organizer_only():
    workspace, event, stage, plan, _, judge_a, _, participant, _ = make_fixture()
    for user in (judge_a, participant):
        client = cookie_client(Session.issue(user).token)
        assert client.get(url(workspace, event, stage, plan, "agreement/")).status_code == 403


def test_agreement_summary_rejects_a_pairwise_mode_plan():
    workspace, event, stage, plan, organizer, _, _, _, _ = make_fixture()
    plan.mode = "pairwise"
    plan.save(update_fields=["mode"])
    client = cookie_client(Session.issue(organizer).token)
    response = client.get(url(workspace, event, stage, plan, "agreement/"))
    assert response.status_code == 400
