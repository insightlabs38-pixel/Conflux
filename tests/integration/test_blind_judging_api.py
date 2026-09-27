import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.anonymize import anonymized_label
from evaluations.models import EvaluationPlan
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
    judge = User.objects.create_user(username="judge_a", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    project = Project.objects.create(
        event=event, name="Team Rocket's Autograder", created_by=organizer
    )
    Submission.objects.create(project=project, stage=stage, updated_by=organizer)
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", draft_criteria=CRITERIA)
    return workspace, event, stage, plan, organizer, judge, project


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def test_candidate_queue_shows_real_name_by_default():
    workspace, event, stage, plan, organizer, judge, project = make_fixture()
    client = cookie_client(Session.issue(judge).token)
    body = client.get(url(workspace, event, stage, plan, "candidates/")).json()
    assert body[0]["name"] == "Team Rocket's Autograder"


def test_candidate_queue_anonymizes_the_name_when_blind_judging_is_enabled():
    workspace, event, stage, plan, organizer, judge, project = make_fixture()
    plan.blind_judging = True
    plan.save(update_fields=["blind_judging"])

    client = cookie_client(Session.issue(judge).token)
    body = client.get(url(workspace, event, stage, plan, "candidates/")).json()
    assert body[0]["name"] == anonymized_label(plan.id, project.public_id)
    assert "Team Rocket" not in body[0]["name"]


def test_anonymized_label_is_stable_and_distinguishes_projects():
    workspace, event, stage, plan, organizer, judge, project = make_fixture()
    second = Project.objects.create(event=event, name="Second entry", created_by=organizer)
    Submission.objects.create(project=second, stage=stage, updated_by=organizer)

    first_label = anonymized_label(plan.id, project.public_id)
    assert first_label == anonymized_label(plan.id, project.public_id)
    assert first_label != anonymized_label(plan.id, second.public_id)
    # A different plan sees a different label for the same project.
    assert first_label != anonymized_label(plan.id + 1, project.public_id)


def test_organizer_can_toggle_blind_judging_via_the_plan_endpoint():
    workspace, event, stage, plan, organizer, judge, project = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    response = client.patch(
        url(workspace, event, stage, plan, ""),
        data={"blind_judging": True},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["blind_judging"] is True
    plan.refresh_from_db()
    assert plan.blind_judging is True
