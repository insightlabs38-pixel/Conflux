from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class LocationKind(models.TextChoices):
    ROOM = "room", "Room"
    TABLE = "table", "Table"
    BOOTH = "booth", "Booth"


class AttendanceMode(models.TextChoices):
    IN_PERSON = "in_person", "In person"
    REMOTE = "remote", "Remote"
    NOT_ATTENDING = "not_attending", "Not attending"


class Location(PublicIdModel):
    """A physical place at the event. Tables and booths may sit inside a room;
    optional floor coordinates (metres) let later tooling reason about distance.
    """

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="locations")
    kind = models.CharField(max_length=10, choices=LocationKind.choices)
    name = models.CharField(max_length=80)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    capacity = models.PositiveSmallIntegerField(null=True, blank=True)
    x = models.FloatField(null=True, blank=True)
    y = models.FloatField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["event", "kind", "name"], name="unique_location_name"),
            models.CheckConstraint(
                condition=models.Q(x__isnull=True, y__isnull=True)
                | models.Q(x__isnull=False, y__isnull=False),
                name="location_coordinates_together",
            ),
        ]

    def clean(self):
        if self.parent_id:
            if self.parent.event_id != self.event_id:
                raise ValidationError({"parent": "Parent belongs to a different event."})
            if self.parent.kind != LocationKind.ROOM or self.kind == LocationKind.ROOM:
                raise ValidationError({"parent": "Only tables and booths can sit inside a room."})
        for name in ("x", "y"):
            value = getattr(self, name)
            if value is not None and not -100000 <= value <= 100000:
                raise ValidationError({name: "Coordinate out of range."})


class Attendance(PublicIdModel):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="attendance")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_attendance"
    )
    mode = models.CharField(max_length=15, choices=AttendanceMode.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="one_attendance_per_person")
        ]


class ProjectLocation(PublicIdModel):
    project = models.OneToOneField(
        "projects.Project", on_delete=models.CASCADE, related_name="location_assignment"
    )
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="projects")
    assigned_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.location.event_id != self.project.event_id:
            raise ValidationError({"location": "Location belongs to a different event."})
        if self.location.kind == LocationKind.ROOM:
            raise ValidationError({"location": "Projects are placed at a table or booth."})


class AgendaSession(PublicIdModel):
    """A scheduled session (talk, workshop, ceremony) on the public agenda. It may
    sit in a room and point at a livestream; the stream is only ever embedded when
    its host is on the embed allow-list (see agenda.embed_url).
    """

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="agenda_sessions"
    )
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions"
    )
    track = models.ForeignKey(
        "events.Track", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    speakers = models.CharField(max_length=300, blank=True)
    stream_url = models.URLField(blank=True)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "title", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="agenda_session_ends_after_start",
            )
        ]

    def clean(self):
        if self.location_id and self.location.event_id != self.event_id:
            raise ValidationError({"location": "Location belongs to a different event."})
        if self.track_id and self.track.event_id != self.event_id:
            raise ValidationError({"track": "Track belongs to a different event."})
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Must be after the start."})
        if self.stream_url:
            from urllib.parse import urlsplit

            parts = urlsplit(self.stream_url)
            if parts.scheme != "https" or parts.username or "@" in parts.netloc:
                raise ValidationError({"stream_url": "Use a plain https:// address."})
