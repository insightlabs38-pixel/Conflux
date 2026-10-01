import uuid

from django.conf import settings
from django.db import models


class PublicIdModel(models.Model):
    """Abstract base giving every domain model a stable, non-sequential public ID.

    Internal primary keys stay auto-incrementing integers for join performance;
    `public_id` is what's ever exposed in URLs/serializers, so nothing outside
    the process can infer row counts or guess adjacent records.
    """

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class IdempotencyKey(models.Model):
    """Records a client-supplied idempotency key so a retried mutation replays
    the original response instead of re-executing the side effect.
    """

    key = models.CharField(max_length=255, unique=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.key


class SavedView(PublicIdModel):
    """A named, reusable way of looking at one entity in one event (PD-F002-B01-T02).

    Stores a query definition (filter tree, sort, columns, density), never rows: running a view
    always goes through the entity query under the *viewer's* authorization, so sharing one cannot
    expose data. `private` views belong to their owner; `organizers` views are visible to everyone
    who may query the entity.
    """

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        ORGANIZERS = "organizers", "Organizers"

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="saved_views")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_views"
    )
    entity = models.SlugField(max_length=60)
    name = models.CharField(max_length=80)
    query = models.JSONField(default=dict)
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "owner", "entity", "name"], name="unique_saved_view_name"
            )
        ]
        ordering = ["name", "id"]


class Job(PublicIdModel):
    """One unit of durable background work (PD-F002-B01-T05); the platform's only job table.

    A feature never adds its own: it registers a *kind* (`core.jobs.register_kind`) and enqueues.
    State moves forward only along `core.jobs.TRANSITIONS`, always under a row lock, so a duplicate
    delivery, a cancel racing a finish and the stale-job sweep cannot disagree. `params` and
    `result` are bounded JSON and never hold secrets; anything larger is a `JobArtifact`.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        CANCELLING = "cancelling", "Cancelling"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="jobs"
    )
    event = models.ForeignKey(
        "events.Event", null=True, blank=True, on_delete=models.CASCADE, related_name="jobs"
    )
    kind = models.SlugField(max_length=60)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    params = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    error = models.JSONField(null=True, blank=True)
    progress_done = models.PositiveIntegerField(null=True, blank=True)
    progress_total = models.PositiveIntegerField(null=True, blank=True)
    progress_message = models.CharField(max_length=200, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs"
    )
    idempotency_key = models.CharField(max_length=100, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requested_by", "kind", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="unique_job_idempotency_key",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["status", "heartbeat_at"]),
        ]
        ordering = ["-created_at", "-id"]


class JobLog(models.Model):
    """A bounded, human-readable trail of a job (the newest `core.jobs.MAX_LOG_LINES`)."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=8, default="info")
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]


class JobArtifact(models.Model):
    """A named output of a job (an export, a report), kept as long as the job."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="artifacts")
    name = models.CharField(max_length=120)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    body = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "name"], name="unique_job_artifact")]
        ordering = ["id"]
