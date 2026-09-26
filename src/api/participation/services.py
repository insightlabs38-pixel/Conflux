from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from policies.models import Action
from policies.services import base_facts, check_action
from stages.models import ParticipationMode, StageEntry

from .models import MAX_TEAM_SIZE, Team, TeamInvite, TeamMembership, TeamMembershipRole


def _team_subject_id(team):
    return str(team.public_id)


def _is_roster_locked(team):
    """True if this team currently holds an active entry in a
    TEAM_LOCKED-mode stage (ST-004) — composition is frozen there, per the
    stage/policy plan doc's "team-locked" stage kind.
    """
    return StageEntry.objects.filter(
        subject_type="team",
        subject_id=_team_subject_id(team),
        exited_at__isnull=True,
        stage__participation_mode=ParticipationMode.TEAM_LOCKED,
    ).exists()


def _ensure_roster_not_locked(team, action_description):
    if _is_roster_locked(team):
        raise ValidationError(f"This team's roster is locked and cannot {action_description}.")


def _ensure_join_is_policy_allowed(team):
    """Server-side, not advisory: an organizer-configured policy (POL-002)
    bound to Action.JOIN can restrict who/when a team may grow, and this
    is checked here — inside join_team itself — so every join path
    (direct or via invite redemption) goes through it identically.
    """
    event = team.event
    allowed, reason = check_action(
        event,
        Action.JOIN,
        base_facts(event),
        subject_type="team",
        subject_id=_team_subject_id(team),
    )
    if not allowed:
        raise ValidationError(reason or "Joining is not currently allowed.")


@transaction.atomic
def create_team(event, name, creator):
    """The creator becomes captain of a brand-new, single-member team."""
    team = Team(event=event, name=name)
    team.full_clean()
    team.save()
    membership = TeamMembership(team=team, user=creator, role=TeamMembershipRole.CAPTAIN)
    membership.full_clean()
    membership.save()
    return team


@transaction.atomic
def join_team(team, user):
    _ensure_roster_not_locked(team, "accept new members")
    _ensure_join_is_policy_allowed(team)
    if team.memberships.count() >= MAX_TEAM_SIZE:
        raise ValidationError(f"Team is full (maximum {MAX_TEAM_SIZE} members).")
    membership = TeamMembership(team=team, user=user, role=TeamMembershipRole.MEMBER)
    membership.full_clean()
    membership.save()
    return membership


@transaction.atomic
def leave_team(team, user):
    """Removes `user`'s membership. An empty team is deleted outright — a
    zero-member team has nothing left to have a captain over. If the
    departing member was captain and the team isn't empty, captaincy
    passes automatically to whoever joined earliest: no team is ever left
    without a captain waiting on a manual reassignment.

    Blocked entirely once the roster is locked (ST-004's team_locked
    stages) — leaving changes composition exactly as joining does.
    """
    _ensure_roster_not_locked(team, "lose members")
    try:
        membership = team.memberships.get(user=user)
    except TeamMembership.DoesNotExist as exc:
        raise ValidationError("Not a member of this team.") from exc

    was_captain = membership.role == TeamMembershipRole.CAPTAIN
    membership.delete()

    remaining = team.memberships.order_by("joined_at")
    if not remaining.exists():
        team.delete()
        return None
    if was_captain:
        new_captain = remaining.first()
        new_captain.role = TeamMembershipRole.CAPTAIN
        new_captain.save(update_fields=["role"])
        return new_captain
    return None


@transaction.atomic
def transfer_captaincy(team, current_captain, new_captain_user):
    try:
        current_membership = team.memberships.get(user=current_captain)
    except TeamMembership.DoesNotExist as exc:
        raise ValidationError("Not a member of this team.") from exc
    if current_membership.role != TeamMembershipRole.CAPTAIN:
        raise ValidationError("Only the current captain can transfer captaincy.")

    try:
        new_membership = team.memberships.get(user=new_captain_user)
    except TeamMembership.DoesNotExist as exc:
        raise ValidationError("The new captain must already be a team member.") from exc

    current_membership.role = TeamMembershipRole.MEMBER
    current_membership.save(update_fields=["role"])
    new_membership.role = TeamMembershipRole.CAPTAIN
    new_membership.save(update_fields=["role"])
    return new_membership


def _require_captain(team, user, action):
    if not team.memberships.filter(user=user, role=TeamMembershipRole.CAPTAIN).exists():
        raise ValidationError(f"Only the team captain can {action}.")


@transaction.atomic
def create_invite(team, creator, *, max_uses=1, ttl=None):
    _require_captain(team, creator, "create invite links")
    invite = TeamInvite(
        team=team,
        created_by=creator,
        max_uses=max_uses,
        expires_at=(timezone.now() + ttl) if ttl else None,
    )
    invite.full_clean()
    invite.save()
    return invite


@transaction.atomic
def revoke_invite(invite, actor):
    _require_captain(invite.team, actor, "revoke invite links")
    invite.revoked_at = timezone.now()
    invite.save(update_fields=["revoked_at"])
    return invite


@transaction.atomic
def redeem_invite(token, user):
    """Joins `user` onto the invite's team. Row-locked for its whole
    duration: two requests racing to redeem the last remaining use of the
    same token must serialize, not both read "still valid" and both
    succeed (a `max_uses=1` invite letting in two people).
    """
    try:
        invite = TeamInvite.objects.select_for_update().get(token=token)
    except TeamInvite.DoesNotExist as exc:
        raise ValidationError("Invalid invite link.") from exc
    if not invite.is_valid():
        raise ValidationError("This invite link has expired or already been used.")

    membership = join_team(invite.team, user)
    invite.use_count += 1
    invite.save(update_fields=["use_count"])
    return membership
