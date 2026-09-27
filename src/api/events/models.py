from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from workspaces.models import Workspace


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
