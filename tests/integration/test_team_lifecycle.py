import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from events.models import Event
from participation.models import MAX_TEAM_SIZE, Team, TeamMembershipRole
from participation.services import create_team, join_team, leave_team, transfer_captaincy
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def make_user(username):
    return User.objects.create_user(username=username, password="unused")


def test_creating_a_team_makes_the_creator_captain():
    event = make_event()
    alice = make_user("alice")
    team = create_team(event, "Nightshift", alice)
    membership = team.memberships.get(user=alice)
    assert membership.role == TeamMembershipRole.CAPTAIN


def test_joining_adds_a_plain_member():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("alice"))
    bob = make_user("bob")
    membership = join_team(team, bob)
    assert membership.role == TeamMembershipRole.MEMBER
    assert team.memberships.count() == 2


def test_a_user_cannot_join_two_teams_in_the_same_event():
    event = make_event()
    team_a = create_team(event, "A", make_user("alice"))
    team_b = create_team(event, "B", make_user("bob"))
    with pytest.raises(ValidationError):
        join_team(team_b, team_a.memberships.get().user)


def test_a_user_can_be_on_different_teams_in_different_events():
    alice = make_user("alice")
    event_a, event_b = make_event("A"), make_event("B")
    create_team(event_a, "Team A", alice)
    team_in_b = create_team(event_b, "Team B", make_user("bob"))
    join_team(team_in_b, alice)  # must not raise
    assert team_in_b.memberships.filter(user=alice).exists()


def test_a_team_cannot_exceed_the_maximum_size():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("captain"))
    for i in range(MAX_TEAM_SIZE - 1):
        join_team(team, make_user(f"member{i}"))
    with pytest.raises(ValidationError, match="full"):
        join_team(team, make_user("one_too_many"))


def test_leaving_as_a_regular_member_does_not_change_the_captain():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    bob = make_user("bob")
    join_team(team, bob)

    leave_team(team, bob)
    assert team.memberships.get(user=captain).role == TeamMembershipRole.CAPTAIN
    assert not team.memberships.filter(user=bob).exists()


def test_the_last_member_leaving_deletes_the_team():
    event = make_event()
    alice = make_user("alice")
    team = create_team(event, "Solo", alice)
    team_id = team.pk

    leave_team(team, alice)

    assert not Team.objects.filter(pk=team_id).exists()


def test_captain_leaving_promotes_the_earliest_remaining_member():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    first_joiner = make_user("first")
    second_joiner = make_user("second")
    join_team(team, first_joiner)
    join_team(team, second_joiner)

    new_captain_membership = leave_team(team, captain)

    assert new_captain_membership.user == first_joiner
    assert team.memberships.get(user=first_joiner).role == TeamMembershipRole.CAPTAIN
    assert team.memberships.get(user=second_joiner).role == TeamMembershipRole.MEMBER


def test_leaving_a_team_you_are_not_on_is_rejected():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("captain"))
    with pytest.raises(ValidationError):
        leave_team(team, make_user("stranger"))


# --- Captaincy transfer --------------------------------------------------


def test_captain_can_transfer_captaincy_to_another_member():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    bob = make_user("bob")
    join_team(team, bob)

    transfer_captaincy(team, captain, bob)

    assert team.memberships.get(user=bob).role == TeamMembershipRole.CAPTAIN
    assert team.memberships.get(user=captain).role == TeamMembershipRole.MEMBER


def test_only_the_captain_can_transfer_captaincy():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    bob = make_user("bob")
    carol = make_user("carol")
    join_team(team, bob)
    join_team(team, carol)

    with pytest.raises(ValidationError, match="Only the current captain"):
        transfer_captaincy(team, bob, carol)


def test_captaincy_cannot_transfer_to_a_non_member():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    outsider = make_user("outsider")

    with pytest.raises(ValidationError, match="already be a team member"):
        transfer_captaincy(team, captain, outsider)
