import secrets

from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from events.models import Event
from projects.models import Project


def _generate_token():
    return secrets.token_urlsafe(24)


class VoteIdentityMode(models.TextChoices):
    AUTHENTICATED = "authenticated", "Authenticated workspace member"
    EMAIL_LINK = "email_link", "Email magic link"
    TOKEN = "token", "Pre-issued token"


class CommentVisibility(models.TextChoices):
    ORGANIZER = "organizer", "Organizer only"
    ORGANIZER_JUDGE = "organizer_judge", "Organizers and judges"
    EVERYONE = "everyone", "Any workspace member"


class VotingPlan(PublicIdModel):
    """Community/audience voting settings for one event (COM-001). Separate
    from evaluations.EvaluationPlan on purpose: this is audience choice, not
    judge scoring -- different identity model, different abuse surface,
    different publication rules.
    """

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="voting_plan")
    identity_mode = models.CharField(
        max_length=20, choices=VoteIdentityMode.choices, default=VoteIdentityMode.AUTHENTICATED
    )
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    allow_comments = models.BooleanField(default=True)
    comment_visibility = models.CharField(
        max_length=20, choices=CommentVisibility.choices, default=CommentVisibility.EVERYONE
    )
    results_published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError({"closes_at": "Must be after opens_at."})

    def is_open(self, at=None):
        at = at or timezone.now()
        return self.opens_at <= at < self.closes_at

    def has_closed(self, at=None):
        at = at or timezone.now()
        return at >= self.closes_at


class VoteToken(PublicIdModel):
    """Anonymous, pre-issued single-use voting token (identity_mode=token):
    e.g. printed on cards handed out at a physical event. Carries no
    identity of its own -- redeeming it is the only fact recorded.
    """

    plan = models.ForeignKey(VotingPlan, on_delete=models.CASCADE, related_name="vote_tokens")
    token = models.CharField(max_length=64, unique=True, default=_generate_token)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class EmailVoteToken(PublicIdModel):
    """One-time magic-link token for identity_mode=email_link. This project
    has no outbound email transport configured (grep the codebase: no
    django.core.mail usage anywhere), so "sending" it is out of scope here
    -- see community.emailing for the explicit, testable seam this is built
    around, and JUDGING.md-equivalent notes in the C-B18 batch report for
    what a real deployment still needs to wire up.
    """

    plan = models.ForeignKey(VotingPlan, on_delete=models.CASCADE, related_name="email_tokens")
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=_generate_token)
    expires_at = models.DateTimeField()
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "email"], name="unique_email_vote_token")
        ]

    def is_valid(self, at=None):
        at = at or timezone.now()
        return self.redeemed_at is None and at < self.expires_at


class Vote(PublicIdModel):
    """One voter's authoritative, immutable ballot (COM-003): exactly one
    vote per voter per plan, enforced by `voter_key` -- what counts as "the
    voter" varies by identity_mode (a user's public_id string, a verified
    email, or a redeemed token's public_id string), but the uniqueness
    contract is identical either way.
    """

    plan = models.ForeignKey(VotingPlan, on_delete=models.PROTECT, related_name="votes")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="community_votes")
    voter_key = models.CharField(max_length=64)
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "voter_key"], name="unique_voter_per_plan")
        ]

    def clean(self):
        if self.project.event_id != self.plan.event_id:
            raise ValidationError({"project": "Project must belong to the plan's event."})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Votes are immutable once cast.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Votes are immutable once cast.")


class Comment(PublicIdModel):
    """A project comment (COM-004). Always tied to a real authenticated
    workspace member -- unlike voting, comments never support the
    email-link/token anonymous identity modes, to keep the abuse surface
    contained (see the C-B18 batch report).
    """

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_comments"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    hidden_at = models.DateTimeField(null=True, blank=True)
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="community_comments_hidden",
    )

    class Meta:
        ordering = ["created_at"]

    def clean(self):
        if not self.body.strip():
            raise ValidationError({"body": "Comment cannot be empty."})
        if len(self.body) > 2000:
            raise ValidationError({"body": "Comment must be at most 2000 characters."})
