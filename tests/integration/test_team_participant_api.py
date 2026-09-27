import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def make_user(username):
    return User.objects.create_user(username=username, password="unused")


def cookie_client(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def make_event_and_members():
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    return workspace, event


def add_member(workspace, username, role=Role.PARTICIPANT):
    user = make_user(username)
    Membership.objects.create(user=user, workspace=workspace, role=role)
    return user


def base_url(workspace, event, suffix):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/{suffix}"


def test_a_participant_with_no_team_sees_the_empty_state():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    response = cookie_client(alice).get(base_url(workspace, event, "my-team/"))
    assert response.status_code == 200
    assert response.json() == {"team": None, "my_role": None}


def test_creating_a_team_makes_the_creator_captain_and_visible_in_status():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    client = cookie_client(alice)

    created = client.post(
        base_url(workspace, event, "my-team/"),
        {"name": "Nightshift"},
        content_type="application/json",
    )
    assert created.status_code == 201

    status = client.get(base_url(workspace, event, "my-team/"))
    assert status.json()["team"]["name"] == "Nightshift"
    assert status.json()["my_role"] == "captain"
    assert len(status.json()["team"]["members"]) == 1


def test_creating_a_second_team_while_already_on_one_is_rejected():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    client = cookie_client(alice)
    client.post(
        base_url(workspace, event, "my-team/"), {"name": "A"}, content_type="application/json"
    )

    second = client.post(
        base_url(workspace, event, "my-team/"), {"name": "B"}, content_type="application/json"
    )
    assert second.status_code == 400


def test_full_invite_and_join_flow():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    bob = add_member(workspace, "bob")
    alice_client = cookie_client(alice)
    alice_client.post(
        base_url(workspace, event, "my-team/"),
        {"name": "Nightshift"},
        content_type="application/json",
    )

    invite = alice_client.post(
        base_url(workspace, event, "my-team/invites/"), {}, content_type="application/json"
    )
    assert invite.status_code == 201
    token = invite.json()["token"]

    bob_client = cookie_client(bob)
    joined = bob_client.post(
        base_url(workspace, event, "team-invites/redeem/"),
        {"token": token},
        content_type="application/json",
    )
    assert joined.status_code == 201
    assert joined.json()["name"] == "Nightshift"

    status = bob_client.get(base_url(workspace, event, "my-team/"))
    assert status.json()["my_role"] == "member"
    assert status.json()["team"]["name"] == "Nightshift"


def test_leaving_a_team_returns_to_the_empty_state():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    client = cookie_client(alice)
    client.post(
        base_url(workspace, event, "my-team/"), {"name": "Solo"}, content_type="application/json"
    )

    left = client.post(base_url(workspace, event, "my-team/leave/"))
    assert left.status_code == 204

    status = client.get(base_url(workspace, event, "my-team/"))
    assert status.json() == {"team": None, "my_role": None}


def test_leaving_without_a_team_is_a_clear_error_not_a_500():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    response = cookie_client(alice).post(base_url(workspace, event, "my-team/leave/"))
    assert response.status_code == 400


def test_transferring_captaincy_via_the_api():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    bob = add_member(workspace, "bob")
    alice_client = cookie_client(alice)
    alice_client.post(
        base_url(workspace, event, "my-team/"),
        {"name": "Nightshift"},
        content_type="application/json",
    )
    invite = alice_client.post(
        base_url(workspace, event, "my-team/invites/"), {}, content_type="application/json"
    )
    cookie_client(bob).post(
        base_url(workspace, event, "team-invites/redeem/"),
        {"token": invite.json()["token"]},
        content_type="application/json",
    )

    transferred = alice_client.post(
        base_url(workspace, event, "my-team/transfer-captain/"),
        {"user": str(bob.public_id)},
        content_type="application/json",
    )
    assert transferred.status_code == 200

    bob_status = cookie_client(bob).get(base_url(workspace, event, "my-team/"))
    assert bob_status.json()["my_role"] == "captain"


def test_revoking_an_invite_prevents_further_redemption():
    workspace, event = make_event_and_members()
    alice = add_member(workspace, "alice")
    bob = add_member(workspace, "bob")
    alice_client = cookie_client(alice)
    alice_client.post(
        base_url(workspace, event, "my-team/"),
        {"name": "Nightshift"},
        content_type="application/json",
    )
    invite = alice_client.post(
        base_url(workspace, event, "my-team/invites/"), {}, content_type="application/json"
    )
    invite_id = invite.json()["public_id"]

    revoked = alice_client.delete(base_url(workspace, event, f"my-team/invites/{invite_id}/"))
    assert revoked.status_code == 204

    redeemed = cookie_client(bob).post(
        base_url(workspace, event, "team-invites/redeem/"),
        {"token": invite.json()["token"]},
        content_type="application/json",
    )
    assert redeemed.status_code == 400


def test_a_stranger_to_the_workspace_cannot_use_team_endpoints():
    workspace, event = make_event_and_members()
    outsider = make_user("outsider")
    response = cookie_client(outsider).get(base_url(workspace, event, "my-team/"))
    assert response.status_code in (401, 403)


def test_member_cannot_read_captains_invite_tokens():
    workspace, event = make_event_and_members()
    captain = add_member(workspace, "captain")
    member = add_member(workspace, "member")
    captain_client = cookie_client(captain)
    captain_client.post(
        base_url(workspace, event, "my-team/"), {"name": "A"}, content_type="application/json"
    )
    invite = captain_client.post(
        base_url(workspace, event, "my-team/invites/"), {}, content_type="application/json"
    )
    cookie_client(member).post(
        base_url(workspace, event, "team-invites/redeem/"),
        {"token": invite.json()["token"]},
        content_type="application/json",
    )

    response = cookie_client(member).get(base_url(workspace, event, "my-team/invites/"))
    assert response.status_code == 400
    assert invite.json()["token"] not in response.content.decode()


def test_invite_cannot_be_redeemed_through_another_event():
    workspace, event = make_event_and_members()
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    captain = add_member(workspace, "captain")
    member = add_member(workspace, "member")
    captain_client = cookie_client(captain)
    captain_client.post(
        base_url(workspace, event, "my-team/"), {"name": "A"}, content_type="application/json"
    )
    invite = captain_client.post(
        base_url(workspace, event, "my-team/invites/"), {}, content_type="application/json"
    )

    response = cookie_client(member).post(
        base_url(workspace, other, "team-invites/redeem/"),
        {"token": invite.json()["token"]},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert cookie_client(member).get(base_url(workspace, event, "my-team/")).json()["team"] is None


def test_invalid_invite_use_count_is_a_validation_error():
    workspace, event = make_event_and_members()
    captain = add_member(workspace, "captain")
    client = cookie_client(captain)
    client.post(
        base_url(workspace, event, "my-team/"), {"name": "A"}, content_type="application/json"
    )
    response = client.post(
        base_url(workspace, event, "my-team/invites/"),
        {"max_uses": "many"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_participant_event_picker_shows_only_published_events_in_own_workspace():
    workspace, event = make_event_and_members()
    member = add_member(workspace, "member")
    event.status = "closed"
    event.is_public = True
    event.save(update_fields=["status", "is_public"])
    Event.objects.create(workspace=workspace, name="Draft", slug="draft", is_public=True)
    other_workspace = Workspace.objects.create(name="Other", slug="other")
    Event.objects.create(
        workspace=other_workspace, name="Other", slug="other", status="closed", is_public=True
    )

    response = cookie_client(member).get(
        f"/api/v1/workspaces/{workspace.public_id}/participant-events/"
    )
    assert response.status_code == 200
    assert response.json() == [{"public_id": str(event.public_id), "name": "Hack"}]
    outsider = make_user("outsider")
    assert cookie_client(outsider).get(
        f"/api/v1/workspaces/{workspace.public_id}/participant-events/"
    ).status_code in (401, 403)


def test_judge_event_picker_includes_private_events_but_requires_judge_role():
    workspace, event = make_event_and_members()
    event.name = "Private final"
    event.status = "closed"
    event.is_public = False
    event.save(update_fields=["name", "status", "is_public"])
    Event.objects.create(workspace=workspace, name="Archived", slug="archived", status="archived")
    other_workspace = Workspace.objects.create(name="Other", slug="other")
    Event.objects.create(workspace=other_workspace, name="Other", slug="other")
    judge = add_member(workspace, "judge", Role.JUDGE)
    participant = add_member(workspace, "participant")
    url = f"/api/v1/workspaces/{workspace.public_id}/judge-events/"
    assert cookie_client(judge).get(url).json() == [
        {"public_id": str(event.public_id), "name": "Private final"}
    ]
    assert cookie_client(participant).get(url).status_code == 403
    assert cookie_client(make_user("stranger")).get(url).status_code in (401, 403)
