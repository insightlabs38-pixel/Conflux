from core.models import PublicIdModel
from django.conf import settings
from django.db import models


class AuditEvent(PublicIdModel):
    """Human-readable evidence: who did what to which resource, when. Written
    in the same transaction as the mutation it documents so it can never
    exist without the mutation, or vice versa.
    """

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100, blank=True, default="")
    target_id = models.CharField(max_length=64, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action}@{self.created_at:%Y-%m-%dT%H:%M:%S}"


class DomainEvent(PublicIdModel):
    """Transactional outbox row: async intent committed atomically with the
    mutation that raised it. A worker (Celery, per ARCHITECTURE.md) polls
    `status=pending` rather than relying on an in-process signal that would
    be lost if the process died between commit and dispatch.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="domain_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.event_type} ({self.status})"
