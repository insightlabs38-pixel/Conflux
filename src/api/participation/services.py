from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MAX_TEAM_SIZE, Team, TeamMembership, TeamMembershipRole


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
    """
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
