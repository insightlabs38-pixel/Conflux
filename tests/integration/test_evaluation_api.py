import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from evaluations.models import Ballot, RubricVersion
from events.models import Event
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 2, "min_score": 0, "max_score": 10},
    {"id": "polish", "name": "Polish", "weight": 1, "min_score": 0, "max_score": 10},
]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge_a = User.objects.create_user(username="judge_a", password="unused")
    judge_b = User.objects.create_user(username="judge_b", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge_a, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=judge_b, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    project = Project.objects.create(event=event, name="Autograder", created_by=organizer)
    return workspace, event, stage, project, organizer, judge_a, judge_b


def plans_url(workspace, event, stage, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{suffix}"
    )


@pytest.mark.django_db(transaction=True)
def test_ballot_and_audit_commit_together_without_a_test_transaction():
    workspace, event, stage, project, organizer, judge, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = organizer_client.post(
        plans_url(workspace, event, stage),
        data={"name": "Panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    ).json()["public_id"]
    assert (
        organizer_client.post(
            plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/")
        ).status_code
        == 201
    )
    response = cookie_client(Session.issue(judge).token).post(
        plans_url(workspace, event, stage, f"{plan_id}/ballots/"),
        data={
            "project": str(project.public_id),
            "responses": [
                {"criterion_id": "impact", "score": 8},
                {"criterion_id": "polish", "score": 6},
            ],
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    assert Ballot.objects.count() == 1
    assert AuditEvent.objects.filter(action="ballot.submitted").count() == 1


def test_organizer_configures_plan_and_publishes_a_rubric_version():
    workspace, event, stage, _, organizer, _, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)

    created = client.post(
        plans_url(workspace, event, stage),
        data={"name": "Judge panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    )
    assert created.status_code == 201
    plan_id = created.json()["public_id"]
    assert created.json()["current_rubric_version"] is None

    published = client.post(
        plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"),
    )
    assert published.status_code == 201
    assert published.json()["number"] == 1
    stored = RubricVersion.objects.get(plan__public_id=plan_id).criteria
    assert [{k: c[k] for k in CRITERIA[0]} for c in stored] == CRITERIA

    republished = client.post(plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"))
    assert republished.json()["number"] == 2


def test_rubric_validation_rejects_bad_weights_and_ranges():
    workspace, event, stage, _, organizer, _, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    bad = client.post(
        plans_url(workspace, event, stage),
        data={
            "name": "Bad",
            "draft_criteria": [
                {"id": "x", "name": "X", "weight": 0, "min_score": 5, "max_score": 1}
            ],
        },
        content_type="application/json",
    )
    assert bad.status_code == 400


def test_judge_can_submit_a_ballot_and_cannot_see_a_peers_ballot():
    workspace, event, stage, project, organizer, judge_a, judge_b = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = organizer_client.post(
        plans_url(workspace, event, stage),
        data={"name": "Judge panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    ).json()["public_id"]
    organizer_client.post(plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"))

    judge_a_client = cookie_client(Session.issue(judge_a).token)
    ballots_url = plans_url(workspace, event, stage, f"{plan_id}/ballots/")
    submitted = judge_a_client.post(
        ballots_url,
        data={
            "project": str(project.public_id),
            "comment": "Solid work",
            "responses": [
                {"criterion_id": "impact", "score": 8},
                {"criterion_id": "polish", "score": 6},
            ],
        },
        content_type="application/json",
    )
    assert submitted.status_code == 201
    assert Ballot.objects.count() == 1

    # A second ballot from the same judge for the same project is rejected.
    dupe = judge_a_client.post(
        ballots_url,
        data={
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": 1}],
        },
        content_type="application/json",
    )
    assert dupe.status_code == 400

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    assert judge_b_client.get(ballots_url).json() == []

    organizer_view = organizer_client.get(ballots_url).json()
    assert len(organizer_view) == 1
    assert organizer_view[0]["comment"] == "Solid work"


def test_ballot_score_out_of_range_is_rejected():
    workspace, event, stage, project, organizer, judge_a, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = organizer_client.post(
        plans_url(workspace, event, stage),
        data={"name": "Judge panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    ).json()["public_id"]
    organizer_client.post(plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"))

    judge_client = cookie_client(Session.issue(judge_a).token)
    response = judge_client.post(
        plans_url(workspace, event, stage, f"{plan_id}/ballots/"),
        data={
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": 99}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


def test_participant_cannot_configure_or_ballot():
    workspace, event, stage, project, organizer, _, _ = make_fixture()
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    client = cookie_client(Session.issue(participant).token)
    assert (
        client.post(
            plans_url(workspace, event, stage), data={}, content_type="application/json"
        ).status_code
        == 403
    )
