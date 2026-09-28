"""PVS10: mentor availability/expertise, a bounded help-request queue and
schedulable office-hours slots. Deliberately not a chat system -- a request
carries a topic and one resolution note, never a message thread; office
hours are a bookable time/place, never a video-call abstraction.
"""

from core.authz import has_any_role
from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event, Track
from workspaces.models import Role


class MentorProfile(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="mentor_profiles")
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    track_expertise = models.ManyToManyField(Track, blank=True, related_name="expert_mentors")
    headline = models.CharField(max_length=200, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "mentor"], name="unique_mentor_profile")
        ]

    def clean(self):
        if not has_any_role(
            self.mentor, self.event.workspace, Role.MENTOR, Role.ORGANIZER, Role.ADMIN
        ):
            raise ValidationError({"mentor": "User must hold the mentor role in this workspace."})


class RequestUrgency(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    URGENT = "urgent", "Urgent"


class RequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CLAIMED = "claimed", "Claimed"
    RESOLVED = "resolved", "Resolved"
    CANCELLED = "cancelled", "Cancelled"


MAX_ACTIVE_REQUESTS_PER_PROJECT = 5


class MentorRequest(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="mentor_requests")
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="mentor_requests"
    )
    track = models.ForeignKey(
        Track, null=True, blank=True, on_delete=models.SET_NULL, related_name="mentor_requests"
    )
    topic = models.CharField(max_length=200)
    urgency = models.CharField(
        max_length=10, choices=RequestUrgency.choices, default=RequestUrgency.NORMAL
    )
    status = models.CharField(
        max_length=10, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mentor_requests_made"
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mentor_requests_claimed",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def clean(self):
        errors = {}
        if self.project_id and self.project.event_id != self.event_id:
            errors["project"] = "Project must belong to this request's event."
        if self.track_id and self.track.event_id != self.event_id:
            errors["track"] = "Track must belong to this request's event."
        if errors:
            raise ValidationError(errors)


class OfficeHourSlot(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="office_hour_slots")
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    track = models.ForeignKey(
        Track, null=True, blank=True, on_delete=models.SET_NULL, related_name="office_hour_slots"
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1), name="office_hour_capacity_positive"
            )
        ]

    def clean(self):
        errors = {}
        if not has_any_role(
            self.mentor, self.event.workspace, Role.MENTOR, Role.ORGANIZER, Role.ADMIN
        ):
            errors["mentor"] = "User must hold the mentor role in this workspace."
        if self.track_id and self.track.event_id != self.event_id:
            errors["track"] = "Track must belong to this slot's event."
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "End time must be after the start time."
        if self.capacity < 1:
            errors["capacity"] = "Capacity must be positive."
        if errors:
            raise ValidationError(errors)


class OfficeHourSignup(PublicIdModel):
    slot = models.ForeignKey(OfficeHourSlot, on_delete=models.CASCADE, related_name="signups")
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="office_hour_signups"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["slot", "project"], name="unique_office_hour_signup")
        ]

    def clean(self):
        if self.project_id and self.slot_id and self.project.event_id != self.slot.event_id:
            raise ValidationError({"project": "Project must belong to the slot's event."})
