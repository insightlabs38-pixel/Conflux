import pytest
from django.core.exceptions import ValidationError
from events.models import Event
from participation.services import create_team, join_team, leave_team, transfer_captaincy
from policies.models import Action, Policy, PolicyBinding
from stages.models import ParticipationMode, Stage, StageEntry
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def make_user(username):
    from accounts.models import User

    return User.objects.create_user(username=username, password="unused")


# --- Stage-lock enforcement ------------------------------------------------


def test_joining_is_blocked_once_the_team_is_in_a_locked_stage():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("captain"))
    locked_stage = Stage.objects.create(
        event=event, name="Finals", participation_mode=ParticipationMode.TEAM_LOCKED
    )
    StageEntry.objects.enter(locked_stage, "team", str(team.public_id))

    with pytest.raises(ValidationError, match="roster is locked"):
        join_team(team, make_user("latecomer"))


def test_leaving_is_blocked_once_the_team_is_in_a_locked_stage():
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    bob = make_user("bob")
    join_team(team, bob)

    locked_stage = Stage.objects.create(
        event=event, name="Finals", participation_mode=ParticipationMode.TEAM_LOCKED
    )
    StageEntry.objects.enter(locked_stage, "team", str(team.public_id))

    with pytest.raises(ValidationError, match="roster is locked"):
        leave_team(team, bob)


def test_captaincy_transfer_is_unaffected_by_a_roster_lock():
    """Locking freezes composition, not who among the existing members
    holds the captain role — transfer_captaincy doesn't change the roster.
    """
    event = make_event()
    captain = make_user("captain")
    team = create_team(event, "Nightshift", captain)
    bob = make_user("bob")
    join_team(team, bob)

    locked_stage = Stage.objects.create(
        event=event, name="Finals", participation_mode=ParticipationMode.TEAM_LOCKED
    )
    StageEntry.objects.enter(locked_stage, "team", str(team.public_id))

    transfer_captaincy(team, captain, bob)  # must not raise
    from participation.models import TeamMembershipRole

    assert team.memberships.get(user=bob).role == TeamMembershipRole.CAPTAIN


def test_joining_is_unaffected_by_a_stage_that_is_not_team_locked():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("captain"))
    open_stage = Stage.objects.create(
        event=event, name="Submission", participation_mode=ParticipationMode.TEAM_FORMATION
    )
    StageEntry.objects.enter(open_stage, "team", str(team.public_id))

    join_team(team, make_user("newcomer"))  # must not raise


def test_a_different_teams_lock_does_not_affect_this_team():
    event = make_event()
    locked_team = create_team(event, "Locked", make_user("captain_a"))
    free_team = create_team(event, "Free", make_user("captain_b"))
    locked_stage = Stage.objects.create(
        event=event, name="Finals", participation_mode=ParticipationMode.TEAM_LOCKED
    )
    StageEntry.objects.enter(locked_stage, "team", str(locked_team.public_id))

    join_team(free_team, make_user("newcomer"))  # must not raise


# --- Policy-gated join -------------------------------------------------


def test_an_organizer_policy_can_deny_joining():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("captain"))
    policy = Policy.objects.create(event=event, name="Closed to new members", ast={"op": "false"})
    PolicyBinding.objects.create(event=event, action=Action.JOIN, policy=policy)

    with pytest.raises(ValidationError, match="Closed to new members"):
        join_team(team, make_user("latecomer"))


def test_an_unbound_join_action_is_unaffected():
    event = make_event()
    team = create_team(event, "Nightshift", make_user("captain"))
    join_team(team, make_user("newcomer"))  # no binding at all: must not raise
