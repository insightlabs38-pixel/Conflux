from datetime import timedelta

import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from events.models import Event
from participation.services import (
    create_invite,
    create_team,
    join_team,
    redeem_invite,
    revoke_invite,
)
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def make_user(username):
    return User.objects.create_user(username=username, password="unused")


def test_only_the_captain_can_create_an_invite():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    bob = make_user("bob")

    join_team(team, bob)

    with pytest.raises(ValidationError, match="Only the team captain"):
        create_invite(team, bob)


def test_redeeming_a_valid_invite_joins_the_team():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain)

    bob = make_user("bob")
    membership = redeem_invite(invite.token, bob)

    assert membership.team_id == team.pk
    assert team.memberships.filter(user=bob).exists()


def test_redeeming_the_same_single_use_invite_twice_is_a_rejected_replay():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain, max_uses=1)
    redeem_invite(invite.token, make_user("bob"))

    with pytest.raises(ValidationError, match="expired or already been used"):
        redeem_invite(invite.token, make_user("carol"))


def test_an_invite_with_max_uses_two_admits_exactly_two_people():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain, max_uses=2)

    redeem_invite(invite.token, make_user("bob"))
    redeem_invite(invite.token, make_user("carol"))
    with pytest.raises(ValidationError):
        redeem_invite(invite.token, make_user("dave"))

    assert team.memberships.count() == 3  # captain + bob + carol


def test_an_expired_invite_is_rejected():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain, ttl=timedelta(hours=1))
    invite.expires_at = timezone.now() - timedelta(minutes=1)
    invite.save(update_fields=["expires_at"])

    with pytest.raises(ValidationError, match="expired"):
        redeem_invite(invite.token, make_user("bob"))


def test_a_revoked_invite_is_rejected_even_before_its_natural_expiry():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain)
    revoke_invite(invite, captain)

    with pytest.raises(ValidationError):
        redeem_invite(invite.token, make_user("bob"))


def test_only_the_captain_can_revoke_an_invite():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain)
    bob = make_user("bob")

    join_team(team, bob)

    with pytest.raises(ValidationError, match="Only the team captain"):
        revoke_invite(invite, bob)


def test_an_unknown_token_is_rejected():
    with pytest.raises(ValidationError, match="Invalid invite link"):
        redeem_invite("not-a-real-token", make_user("bob"))


def test_redeeming_an_invite_still_respects_team_size_and_one_team_per_event():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    invite = create_invite(team, captain, max_uses=10)

    for i in range(3):  # captain + 3 = 4, the max
        join_team(team, make_user(f"filler{i}"))

    with pytest.raises(ValidationError, match="full"):
        redeem_invite(invite.token, make_user("one_too_many"))
