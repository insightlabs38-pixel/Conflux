from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from community import abuse, voting
from community.models import AbuseSignal, RateLimitEvent, Vote, VoteToken
from django.test import Client
from django.utils import timezone
from events.models import Event, EventStatus
from test_voting_flows import cookie_client, make_public_event_with_projects, open_plan, votes_url
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def post_vote(client, url, project, token=None):
    data = {"project": str(project.public_id)}
    if token is not None:
        data["token"] = token
    return client.post(url, data, content_type="application/json")


def test_vote_attempt_limit_boundary_and_window_recovery(monkeypatch):
    workspace, event, _, projects = make_public_event_with_projects()
    plan = open_plan(event, identity_mode="token")
    monkeypatch.setattr(voting, "VOTE_ATTEMPT_IP_LIMIT", (2, timedelta(minutes=10)))
    client = Client()
    url = votes_url(workspace, event)
    tokens = [VoteToken.objects.create(plan=plan) for _ in range(3)]

    assert post_vote(client, url, projects[0], tokens[0].token).status_code == 201
    assert post_vote(client, url, projects[0], tokens[1].token).status_code == 201
    blocked = post_vote(client, url, projects[0], tokens[2].token)
    assert blocked.status_code == 400
    assert "Too many attempts" in str(blocked.json())
    assert Vote.objects.count() == 2
    tokens[2].refresh_from_db()
    assert tokens[2].redeemed_at is None
    assert RateLimitEvent.objects.count() == 2
    assert AbuseSignal.objects.filter(plan=plan, signal_type="rate_limit_exceeded").count() == 1

    RateLimitEvent.objects.update(created_at=timezone.now() - timedelta(minutes=11))
    assert post_vote(client, url, projects[0], tokens[2].token).status_code == 201
    assert Vote.objects.count() == 3


def test_email_case_variants_cannot_cast_two_ballots():
    workspace, event, _, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="email_link")
    client = Client()
    request_url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        "/voting/request-email-token/"
    )
    first = client.post(
        request_url, {"email": " Voter@Example.com "}, content_type="application/json"
    )
    assert first.status_code == 201
    assert (
        post_vote(
            client, votes_url(workspace, event), projects[0], first.json()["token"]
        ).status_code
        == 201
    )
    second = client.post(
        request_url, {"email": "voter@example.com"}, content_type="application/json"
    )
    assert second.status_code == 201
    duplicate = post_vote(client, votes_url(workspace, event), projects[1], second.json()["token"])
    assert duplicate.status_code == 400
    assert "already voted" in str(duplicate.json())
    assert Vote.objects.count() == 1
    assert all(
        "voter@example.com" not in str(event.metadata).casefold()
        for event in AuditEvent.objects.filter(action="email_vote_token.requested")
    )


def test_email_request_limit_counts_canonical_address_and_recovers(monkeypatch):
    workspace, event, _, _ = make_public_event_with_projects()
    plan = open_plan(event, identity_mode="email_link")
    monkeypatch.setattr(voting, "EMAIL_TOKEN_REQUEST_LIMIT", (2, timedelta(minutes=10)))
    url = f"/api/v1/public/events/{event.public_id}/voting/request-email-token/"
    client = Client()
    for address in ("Voter@Example.com", "voter@example.com"):
        assert (
            client.post(url, {"email": address}, content_type="application/json").status_code == 201
        )
    blocked = client.post(url, {"email": "VOTER@example.com"}, content_type="application/json")
    assert blocked.status_code == 400
    assert AbuseSignal.objects.filter(plan=plan, signal_type="rate_limit_exceeded").count() == 1
    RateLimitEvent.objects.update(created_at=timezone.now() - timedelta(minutes=11))
    assert (
        client.post(
            url, {"email": "voter@example.com"}, content_type="application/json"
        ).status_code
        == 201
    )


def test_rotated_email_token_cannot_be_replayed():
    workspace, event, _, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="email_link")
    client = Client()
    request_url = f"/api/v1/public/events/{event.public_id}/voting/request-email-token/"
    first = client.post(
        request_url, {"email": "voter@example.com"}, content_type="application/json"
    )
    second = client.post(
        request_url, {"email": "voter@example.com"}, content_type="application/json"
    )
    assert first.status_code == second.status_code == 201
    assert (
        post_vote(
            client, votes_url(workspace, event), projects[0], first.json()["token"]
        ).status_code
        == 400
    )
    assert (
        post_vote(
            client, votes_url(workspace, event), projects[0], second.json()["token"]
        ).status_code
        == 201
    )
    assert Vote.objects.count() == 1


def test_workspace_route_and_cross_event_token_are_isolated():
    workspace, event, _, projects = make_public_event_with_projects()
    plan = open_plan(event, identity_mode="token")
    token = VoteToken.objects.create(plan=plan)
    wrong_workspace = Workspace.objects.create(name="Other", slug="other")
    wrong_url = votes_url(wrong_workspace, event)
    assert post_vote(Client(), wrong_url, projects[0], token.token).status_code == 404

    other_event = Event.objects.create(
        workspace=workspace,
        name="Other event",
        slug="other-event",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    open_plan(other_event, identity_mode="token")
    # A token issued for another event must not authorize a vote here.
    foreign_token = VoteToken.objects.create(plan=other_event.voting_plan)
    assert (
        post_vote(
            Client(), votes_url(workspace, event), projects[0], foreign_token.token
        ).status_code
        == 400
    )
    assert Vote.objects.count() == 0
    assert (
        post_vote(Client(), votes_url(workspace, event), projects[0], token.token).status_code
        == 201
    )


def test_authenticated_nonmember_cannot_vote():
    workspace, event, _, projects = make_public_event_with_projects()
    open_plan(event, identity_mode="authenticated")
    outsider = User.objects.create_user(username="outsider", password="unused")
    client = cookie_client(Session.issue(outsider).token)
    assert post_vote(client, votes_url(workspace, event), projects[0]).status_code == 403
    assert Vote.objects.count() == 0


def test_rate_limit_scope_is_per_plan():
    workspace, event, _, _ = make_public_event_with_projects()
    first_plan = open_plan(event)
    other_event = Event.objects.create(
        workspace=workspace,
        name="Second",
        slug="second",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    second_plan = open_plan(other_event)
    window = timedelta(minutes=10)
    abuse.enforce_rate_limit(first_plan, "vote_attempt", "127.0.0.1", limit=1, window=window)
    abuse.enforce_rate_limit(second_plan, "vote_attempt", "127.0.0.1", limit=1, window=window)
    assert RateLimitEvent.objects.count() == 2
