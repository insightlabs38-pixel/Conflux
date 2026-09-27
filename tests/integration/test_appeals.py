import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import EvaluationPlan, NormalizationRun
from events.models import Event
from projects.models import Project, ProjectMembership, ProjectMembershipRole
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def fixture():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    owner = User.objects.create_user(username="owner")
    outsider = User.objects.create_user(username="outsider")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=owner, role=Role.PARTICIPANT)
    Membership.objects.create(workspace=workspace, user=outsider, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Final")
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel")
    project = Project.objects.create(event=event, created_by=organizer, name="Entry")
    ProjectMembership.objects.create(project=project, user=owner, role=ProjectMembershipRole.OWNER)
    return workspace, organizer, owner, outsider, event, stage, plan, project


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/appeals/{suffix}"
    )


def publish_results(plan):
    run = NormalizationRun.objects.create(
        plan=plan,
        number=1,
        ridge_lambda=0.0,
        iterations=0,
        converged=True,
        grand_mean=0.0,
        evidence={},
    )
    plan.published_normalization_run = run
    plan.results_visible_to_participants = True
    plan.save(update_fields=["published_normalization_run", "results_visible_to_participants"])


def test_appeal_requires_published_visible_results():
    workspace, organizer, owner, outsider, event, stage, plan, project = fixture()
    appeals_url = url(workspace, event, stage, plan)
    early = client(owner).post(
        appeals_url,
        {"project": str(project.public_id), "body": "Too early"},
        content_type="application/json",
    )
    assert early.status_code == 400

    publish_results(plan)
    filed = client(owner).post(
        appeals_url,
        {"project": str(project.public_id), "body": "The rubric criterion was misapplied."},
        content_type="application/json",
    )
    assert filed.status_code == 201
    assert filed.json()["status"] == "pending"
    assert filed.json()["submitted_by_username"] == "owner"


def test_only_a_project_member_can_appeal_and_participants_see_only_their_own():
    workspace, organizer, owner, outsider, event, stage, plan, project = fixture()
    publish_results(plan)
    appeals_url = url(workspace, event, stage, plan)

    assert (
        client(outsider)
        .post(
            appeals_url,
            {"project": str(project.public_id), "body": "Not mine"},
            content_type="application/json",
        )
        .status_code
        == 404
    )
    assert (
        client(organizer)
        .post(
            appeals_url,
            {"project": str(project.public_id), "body": "Organizer filing"},
            content_type="application/json",
        )
        .status_code
        == 403
    )

    client(owner).post(
        appeals_url,
        {"project": str(project.public_id), "body": "The rubric criterion was misapplied."},
        content_type="application/json",
    )
    assert len(client(organizer).get(appeals_url).json()) == 1
    assert len(client(owner).get(appeals_url).json()) == 1
    assert client(outsider).get(appeals_url).json() == []


def test_organizer_decides_an_appeal_exactly_once():
    workspace, organizer, owner, outsider, event, stage, plan, project = fixture()
    publish_results(plan)
    appeals_url = url(workspace, event, stage, plan)
    created = client(owner).post(
        appeals_url,
        {"project": str(project.public_id), "body": "The rubric criterion was misapplied."},
        content_type="application/json",
    )
    appeal_id = created.json()["public_id"]
    decide_url = url(workspace, event, stage, plan, f"{appeal_id}/decide/")

    assert (
        client(owner)
        .post(decide_url, {"status": "upheld"}, content_type="application/json")
        .status_code
        == 403
    )

    decided = client(organizer).post(
        decide_url,
        {"status": "overturned", "decision_note": "Rubric miscount confirmed."},
        content_type="application/json",
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "overturned"
    assert decided.json()["decided_by"] == "organizer"

    redecided = client(organizer).post(
        decide_url, {"status": "upheld"}, content_type="application/json"
    )
    assert redecided.status_code == 400
