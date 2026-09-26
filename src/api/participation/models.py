from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event

MAX_TEAM_SIZE = 4  # "Team size one to four" — official rule, not a house choice.


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
