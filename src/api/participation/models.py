import secrets

from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from events.models import Event

MAX_TEAM_SIZE = 4  # "Team size one to four" — official rule, not a house choice.


def _generate_invite_token():
    return secrets.token_urlsafe(24)


class Team(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_team_name_event")
        ]

    def __str__(self):
        return self.name


class TeamMembershipRole(models.TextChoices):
    MEMBER = "member", "Member"
    CAPTAIN = "captain", "Captain"


class TeamMembership(PublicIdModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships"
    )
    role = models.CharField(
        max_length=10, choices=TeamMembershipRole.choices, default=TeamMembershipRole.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Team size is enforced in services.join_team (a count check
            # can't be a DB constraint); this constraint is the one thing
            # the DB *can* guarantee: no duplicate row for the same pairing.
            models.UniqueConstraint(fields=["team", "user"], name="unique_team_membership"),
        ]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user_id}@{self.team_id}:{self.role}"

    def clean(self):
        # A user is on at most one team per event — "solo is welcome" reads
        # as exactly one team, not zero-or-many. Excludes this row itself
        # so re-saving an existing membership (e.g. a role change) doesn't
        # trip over its own prior state.
        conflicting = (
            TeamMembership.objects.filter(team__event=self.team.event, user=self.user)
            .exclude(pk=self.pk)
            .exists()
        )
        if conflicting:
            raise ValidationError("Already a member of a team in this event.")


class TeamInvite(PublicIdModel):
    """A redeemable link a captain hands out for T1 "team formation by
    invite link". `max_uses`/`use_count` are the replay control: once a
    token has been redeemed `max_uses` times, redeeming it again is a
    replay of an already-spent invite, not a new join, and is rejected —
    checked and incremented under a row lock (services.redeem_invite) so
    two concurrent redemptions of the last remaining use can't both
    succeed.
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invites")
    token = models.CharField(max_length=64, unique=True, default=_generate_invite_token)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_team_invites",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=1)
    use_count = models.PositiveIntegerField(default=0)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"invite:{self.team_id}:{self.token[:8]}"

    def is_valid(self, at=None):
        now = at or timezone.now()
        if self.revoked_at is not None:
            return False
        if self.expires_at and now >= self.expires_at:
            return False
        return self.use_count < self.max_uses


class MarketplaceProfile(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="marketplace_profiles")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="marketplace_profiles"
    )
    skills = models.JSONField(default=list, blank=True)
    # VS16: participant-controlled matching signals beyond skills, all
    # optional -- an unset roles/interests list or a null availability
    # simply contributes no match evidence rather than excluding the
    # profile from any listing (additive, same as `skills` always was).
    roles = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    availability_hours_per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    bio = models.CharField(max_length=500, blank=True)
    visible = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="unique_marketplace_profile")
        ]


class TeamOpening(PublicIdModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="marketplace_openings")
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_openings",
    )
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=500, blank=True)
    desired_skills = models.JSONField(default=list, blank=True)
    desired_roles = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    min_availability_hours_per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.project_id and self.project.team_id != self.team_id:
            raise ValidationError({"project": "Project must belong to this team."})
