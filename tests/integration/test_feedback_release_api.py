import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from projects.models import Project, ProjectMembership, ProjectMembershipRole
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
    judge = User.objects.create_user(username="judge", password="unused")
    owner = User.objects.create_user(username="owner", password="unused")
    outsider = User.objects.create_user(username="outsider", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=owner, workspace=workspace, role=Role.PARTICIPANT)
    Membership.objects.create(user=outsider, workspace=workspace, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    project = Project.objects.create(event=event, name="Autograder", created_by=owner)
    ProjectMembership.objects.create(project=project, user=owner, role=ProjectMembershipRole.OWNER)
    return workspace, event, stage, project, organizer, judge, owner, outsider


def plans_url(workspace, event, stage, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{suffix}"
    )


def feedback_url(workspace, event, stage, plan_id, project):
    return plans_url(workspace, event, stage, f"{plan_id}/feedback/{project.public_id}/")


def submit_ballot(client, workspace, event, stage, plan_id, project, comment):
    return client.post(
        plans_url(workspace, event, stage, f"{plan_id}/ballots/"),
        data={
            "project": str(project.public_id),
            "comment": comment,
            "responses": [{"criterion_id": "impact", "score": 8}],
        },
        content_type="application/json",
    )


def make_published_plan(organizer_client, workspace, event, stage):
    plan_id = organizer_client.post(
        plans_url(workspace, event, stage),
        data={"name": "Panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    ).json()["public_id"]
    organizer_client.post(plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"))
    return plan_id


def test_feedback_is_hidden_from_the_owner_until_the_organizer_releases_it():
    workspace, event, stage, project, organizer, judge, owner, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = make_published_plan(organizer_client, workspace, event, stage)
    submit_ballot(
        cookie_client(Session.issue(judge).token),
        workspace,
        event,
        stage,
        plan_id,
        project,
        "Great use of caching.",
    )

    owner_client = cookie_client(Session.issue(owner).token)
    hidden = owner_client.get(feedback_url(workspace, event, stage, plan_id, project))
    assert hidden.status_code == 403

    # The organizer can always read it, release gate or not.
    organizer_view = organizer_client.get(feedback_url(workspace, event, stage, plan_id, project))
    assert organizer_view.status_code == 200
    assert organizer_view.json()[0]["comment"] == "Great use of caching."


def test_released_feedback_is_anonymous_by_default_and_scoped_to_the_project_owner():
    workspace, event, stage, project, organizer, judge, owner, outsider = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = make_published_plan(organizer_client, workspace, event, stage)
    submit_ballot(
        cookie_client(Session.issue(judge).token),
        workspace,
        event,
        stage,
        plan_id,
        project,
        "Great use of caching.",
    )
    organizer_client.patch(
        plans_url(workspace, event, stage, f"{plan_id}/"),
        {"feedback_visible_to_participants": True},
        content_type="application/json",
    )

    owner_client = cookie_client(Session.issue(owner).token)
    released = owner_client.get(feedback_url(workspace, event, stage, plan_id, project))
    assert released.status_code == 200
    entry = released.json()[0]
    assert entry["comment"] == "Great use of caching."
    assert entry["judge"] is None

    outsider_client = cookie_client(Session.issue(outsider).token)
    assert (
        outsider_client.get(feedback_url(workspace, event, stage, plan_id, project)).status_code
        == 404
    )


def test_organizer_can_opt_out_of_anonymity():
    workspace, event, stage, project, organizer, judge, owner, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = make_published_plan(organizer_client, workspace, event, stage)
    submit_ballot(
        cookie_client(Session.issue(judge).token),
        workspace,
        event,
        stage,
        plan_id,
        project,
        "Great use of caching.",
    )
    organizer_client.patch(
        plans_url(workspace, event, stage, f"{plan_id}/"),
        {"feedback_visible_to_participants": True, "feedback_anonymous": False},
        content_type="application/json",
    )

    owner_client = cookie_client(Session.issue(owner).token)
    entry = owner_client.get(feedback_url(workspace, event, stage, plan_id, project)).json()[0]
    assert entry["judge"] == "judge"


def test_a_ballot_with_no_comment_is_never_shown():
    workspace, event, stage, project, organizer, judge, owner, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = make_published_plan(organizer_client, workspace, event, stage)
    submit_ballot(
        cookie_client(Session.issue(judge).token), workspace, event, stage, plan_id, project, ""
    )
    organizer_client.patch(
        plans_url(workspace, event, stage, f"{plan_id}/"),
        {"feedback_visible_to_participants": True},
        content_type="application/json",
    )

    owner_client = cookie_client(Session.issue(owner).token)
    assert owner_client.get(feedback_url(workspace, event, stage, plan_id, project)).json() == []
