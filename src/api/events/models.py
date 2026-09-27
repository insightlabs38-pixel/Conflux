import secrets

from core.authz import has_any_role
from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from workspaces.models import Role, Workspace


class EventStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


# Every status an unauthenticated visitor may ever reach (S19): once an
# organizer opens an event it stays publicly readable through closing and
# archiving, so the public site becomes a stable post-event archive instead
# of 404ing the moment judging ends. Only DRAFT (never announced) is hidden.
PUBLICLY_VISIBLE_STATUSES = [EventStatus.OPEN, EventStatus.CLOSED, EventStatus.ARCHIVED]


class Event(PublicIdModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="events")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=EventStatus.choices, default=EventStatus.DRAFT)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "slug"], name="unique_event_slug_workspace"
            )
        ]
        ordering = ["-created_at"]

    def clean(self):
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "End must be after start."})
        if self.status == EventStatus.OPEN:
            if not self.starts_at or not self.ends_at:
                raise ValidationError(
                    {"status": "Start and end dates are required to open an event."}
                )
            if self.ends_at <= timezone.now():
                raise ValidationError({"ends_at": "An event cannot open after its end date."})


class Track(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tracks")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_track_name_event")
        ]
        ordering = ["position", "id"]


class BasePrize(PublicIdModel):
    class Kind(models.TextChoices):
        CASH = "cash", "Cash"
        CREDIT = "credit", "Credit"
        DISCOUNT = "discount", "Discount"
        SUBSCRIPTION = "subscription", "Subscription"
        HARDWARE = "hardware", "Hardware"
        TRAVEL = "travel", "Travel"
        SERVICE = "service", "Service"
        MENTORSHIP = "mentorship", "Mentorship"
        SWAG = "swag", "Swag"
        OTHER = "other", "Other"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="base_prizes")
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL, null=True, blank=True, related_name="base_prizes"
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def clean(self):
        errors = {}
        if self.track_id and self.track.event_id != self.event_id:
            errors["track"] = "Track must belong to this event."
        if self.kind == self.Kind.CASH and (self.amount is None or not self.currency):
            errors["amount"] = "Cash prizes require an amount and currency."
        if self.amount is not None and self.amount < 0:
            errors["amount"] = "Amount must be nonnegative."
        if self.kind != self.Kind.CASH and (self.amount is not None or self.currency):
            errors["amount"] = "Only cash prizes may have an amount or currency."
        if errors:
            raise ValidationError(errors)


class RegistrationMode(models.TextChoices):
    OPEN = "open", "Open — anyone can register"
    APPLICATION = "application", "Application — organizer reviews each request"
    INVITE_ONLY = "invite_only", "Invite only — a code is required"


class EventRegistrationSettings(PublicIdModel):
    """One organizer-tunable policy per event (VS17): how someone becomes a
    PARTICIPANT here. Capacity/waitlist are counted against this event's own
    `EventApplication` rows, not workspace `Membership` -- a workspace can
    host several events (see VS15's cross-event fixtures) and Membership's
    PARTICIPANT role is workspace-wide, so per-event capacity has to live on
    the event-scoped record that actually tracks "applied to this event".
    """

    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, related_name="registration_settings"
    )
    mode = models.CharField(
        max_length=20, choices=RegistrationMode.choices, default=RegistrationMode.OPEN
    )
    capacity = models.PositiveIntegerField(null=True, blank=True)
    waitlist_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


def _generate_registration_code():
    return secrets.token_urlsafe(9)


class RegistrationInviteCode(PublicIdModel):
    """A redeemable code for INVITE_ONLY registration -- same
    validity/replay shape as `participation.TeamInvite`."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registration_invite_codes"
    )
    code = models.CharField(max_length=32, unique=True, default=_generate_registration_code)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    max_uses = models.PositiveIntegerField(default=1)
    use_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.revoked_at is None and self.use_count < self.max_uses


class RegistrationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    WAITLISTED = "waitlisted", "Waitlisted"
    REJECTED = "rejected", "Rejected"


class EventApplication(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="applications")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_applications"
    )
    status = models.CharField(
        max_length=12, choices=RegistrationStatus.choices, default=RegistrationStatus.PENDING
    )
    note = models.CharField(max_length=500, blank=True)
    invite_code = models.ForeignKey(
        RegistrationInviteCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="applications",
    )
    waitlist_position = models.PositiveIntegerField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="unique_event_application")
        ]
        ordering = ["created_at", "id"]

    def clean(self):
        if self.invite_code_id and self.invite_code.event_id != self.event_id:
            raise ValidationError({"invite_code": "Invite code must belong to this event."})


class Announcement(PublicIdModel):
    """An organizer broadcast shown on the public site's live "announcements"
    block (VS22) -- the same "live, no organizer content of its own"
    treatment as `schedule`/`gallery`/`results` blocks: this data always
    reflects real posts, so there is nothing here for a page-builder
    rewrite to go stale against.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=160)
    body = models.TextField(max_length=4000, blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class ParticipantCheckIn(PublicIdModel):
    """A volunteer's record that a participant physically showed up
    (VS18) -- purely an attendance log, no effect on Membership, teams,
    or judging.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="check_ins")
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_check_ins"
    )
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    checked_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "participant"], name="unique_event_check_in")
        ]
        ordering = ["-checked_in_at", "-id"]

    def clean(self):
        if not has_any_role(self.participant, self.event.workspace, Role.PARTICIPANT):
            raise ValidationError(
                {"participant": "User must hold the participant role in this workspace."}
            )
