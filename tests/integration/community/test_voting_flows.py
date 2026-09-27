from datetime import timedelta

import pytest
from accounts.models import Session, User
from community.models import EmailVoteToken, Vote, VoteToken, VotingPlan
from django.test import Client
from django.utils import timezone
from events.models import Event, EventStatus
from projects.models import Project, Submission, SubmissionStatus, SubmissionVersion
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_public_event_with_projects(n=2):
    organizer = User.objects.create_user(username="organizer", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(
        workspace=workspace,
        name="Hack",
        slug="hack",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(n):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        submission = Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        version = SubmissionVersion.objects.create(
            submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=organizer
        )
        submission.status = SubmissionStatus.FINALIZED
        submission.current_version = version
        submission.save()
        projects.append(project)
    return workspace, event, organizer, projects


def open_plan(event, **overrides):
    now = timezone.now()
    defaults = {"opens_at": now - timedelta(hours=1), "closes_at": now + timedelta(hours=1)}
    defaults.update(overrides)
    return VotingPlan.objects.create(event=event, **defaults)


def votes_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/voting/votes/"


def test_authenticated_voter_can_vote_once_and_a_second_attempt_is_rejected():
    workspace, event, organizer, projects = make_public_event_with_projects()
    voter = User.objects.create_user(username="voter", password="unused")
    Membership.objects.create(user=voter, workspace=workspace, role=Role.PARTICIPANT)
    open_plan(event, identity_mode="authenticated")
    client = cookie_client(Session.issue(voter).token)

    first = client.post(
        votes_url(workspace, event),
        {"project": str(projects[0].public_id)},
        content_type="application/json",
    )
    assert first.status_code == 201
    assert Vote.objects.count() == 1

    second = client.post(
        votes_url(workspace, event),
        {"project": str(projects[1].public_id)},
        content_type="application/json",
    )
    assert second.status_code == 400
    assert Vote.objects.count() == 1


def test_anonymous_visitor_is_rejected_under_authenticated_mode():
    workspace, event, organizer, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="authenticated")
    response = Client().post(
        votes_url(workspace, event),
        {"project": str(projects[0].public_id)},
        content_type="application/json",
    )
    assert response.status_code in (401, 403)


def test_email_link_voting_requests_a_token_and_redeems_it_exactly_once():
    workspace, event, organizer, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="email_link")
    client = Client()

    requested = client.post(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/voting/request-email-token/",
        {"email": "voter@example.com"},
        content_type="application/json",
    )
    assert requested.status_code == 201
    token_value = requested.json()["token"]

    cast = client.post(
        votes_url(workspace, event),
        {"project": str(projects[0].public_id), "token": token_value},
        content_type="application/json",
    )
    assert cast.status_code == 201

    reuse = client.post(
        votes_url(workspace, event),
        {"project": str(projects[1].public_id), "token": token_value},
        content_type="application/json",
    )
    assert reuse.status_code == 400
    assert Vote.objects.count() == 1


def test_requesting_a_new_email_token_replaces_the_old_one():
    workspace, event, organizer, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="email_link")
    client = Client()
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        "/voting/request-email-token/"
    )
    first_token = client.post(
        url, {"email": "voter@example.com"}, content_type="application/json"
    ).json()["token"]
    second_token = client.post(
        url, {"email": "voter@example.com"}, content_type="application/json"
    ).json()["token"]
    assert first_token != second_token
    assert EmailVoteToken.objects.filter(email="voter@example.com").count() == 1


def test_pre_issued_token_voting_is_single_use_and_anonymous():
    workspace, event, organizer, projects = make_public_event_with_projects()
    plan = open_plan(event, identity_mode="token")
    token = VoteToken.objects.create(plan=plan)
    client = Client()

    cast = client.post(
        votes_url(workspace, event),
        {"project": str(projects[0].public_id), "token": token.token},
        content_type="application/json",
    )
    assert cast.status_code == 201
    token.refresh_from_db()
    assert token.redeemed_at is not None

    reuse = client.post(
        votes_url(workspace, event),
        {"project": str(projects[1].public_id), "token": token.token},
        content_type="application/json",
    )
    assert reuse.status_code == 400


def test_voting_outside_the_window_is_rejected():
    workspace, event, organizer, projects = make_public_event_with_projects()
    now = timezone.now()
    open_plan(
        event,
        identity_mode="authenticated",
        opens_at=now + timedelta(hours=1),
        closes_at=now + timedelta(hours=2),
    )
    voter = User.objects.create_user(username="voter", password="unused")
    Membership.objects.create(user=voter, workspace=workspace, role=Role.PARTICIPANT)
    client = cookie_client(Session.issue(voter).token)
    response = client.post(
        votes_url(workspace, event),
        {"project": str(projects[0].public_id)},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert Vote.objects.count() == 0


def test_candidate_order_endpoint_returns_all_public_projects_and_is_workable_anonymously():
    workspace, event, organizer, projects = make_public_event_with_projects(n=3)
    open_plan(event)
    response = Client().get(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/voting/candidates/"
    )
    assert response.status_code == 200
    assert {c["project"] for c in response.json()} == {str(p.public_id) for p in projects}


def test_voting_is_also_reachable_without_knowing_the_workspace_id():
    workspace, event, organizer, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="token")
    from community.models import VoteToken

    plan = event.voting_plan
    token = VoteToken.objects.create(plan=plan)
    client = Client()

    public_base = f"/api/v1/public/events/{event.public_id}/voting"
    candidates = client.get(public_base + "/candidates/")
    assert candidates.status_code == 200
    assert {c["project"] for c in candidates.json()} == {str(p.public_id) for p in projects}

    cast = client.post(
        public_base + "/votes/",
        {"project": str(projects[0].public_id), "token": token.token},
        content_type="application/json",
    )
    assert cast.status_code == 201


def test_public_status_endpoint_reveals_identity_mode_and_window_but_nothing_organizer_only():
    workspace, event, organizer, projects = make_public_event_with_projects()
    plan = open_plan(event, identity_mode="email_link")

    status_url = f"/api/v1/public/events/{event.public_id}/voting/status/"
    body = Client().get(status_url).json()
    assert body["identity_mode"] == "email_link"
    assert body["is_open"] is True
    assert "results_published_at" not in body

    plan.delete()
    assert Client().get(status_url).json() is None
