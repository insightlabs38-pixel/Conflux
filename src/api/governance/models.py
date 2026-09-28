"""PVS11: participant-facing governance. Every record here either is
immutable evidence (rules versions, receipts, corrections) or a request/response
that feeds an existing mechanism (ExceptionGrant, ConflictOfInterest,
ResultsPublish) rather than a parallel one.
"""

from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event


class ImmutableMixin(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError(f"{type(self).__name__} records are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(f"{type(self).__name__} records are immutable.")


class GovernanceSettings(PublicIdModel):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="governance")
    require_publication_approval = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    read_only_message = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class RulesVersion(ImmutableMixin, PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rules_versions")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["event", "number"], name="unique_rules_version")
        ]


class RulesAcknowledgement(ImmutableMixin, PublicIdModel):
    version = models.ForeignKey(RulesVersion, on_delete=models.PROTECT, related_name="acks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["version", "user"], name="unique_rules_ack")]


class RequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


class PublicationRequest(PublicIdModel):
    plan = models.ForeignKey(
        "evaluations.EvaluationPlan", on_delete=models.CASCADE, related_name="publication_requests"
    )
    normalization_run = models.ForeignKey(
        "evaluations.NormalizationRun", on_delete=models.PROTECT, related_name="+"
    )
    tie_breaks = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=12, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    decision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan"],
                condition=models.Q(status="pending"),
                name="one_pending_publication_request_per_plan",
            )
        ]


class ResultCorrection(ImmutableMixin, PublicIdModel):
    plan = models.ForeignKey(
        "evaluations.EvaluationPlan", on_delete=models.CASCADE, related_name="corrections"
    )
    previous_run = models.ForeignKey(
        "evaluations.NormalizationRun", null=True, on_delete=models.PROTECT, related_name="+"
    )
    run = models.ForeignKey(
        "evaluations.NormalizationRun", on_delete=models.PROTECT, related_name="+"
    )
    reason = models.TextField(blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class AssignmentResponseStatus(models.TextChoices):
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"


class AssignmentResponse(PublicIdModel):
    assignment = models.OneToOneField(
        "evaluations.Assignment", on_delete=models.CASCADE, related_name="response"
    )
    status = models.CharField(max_length=10, choices=AssignmentResponseStatus.choices)
    reason = models.TextField(blank=True)
    responded_at = models.DateTimeField(auto_now=True)


class DeadlineExceptionRequest(PublicIdModel):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="deadline_exception_requests"
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="deadline_exception_requests"
    )
    action = models.CharField(max_length=20, default="submit")
    reason = models.TextField()
    status = models.CharField(
        max_length=12, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    decision_note = models.TextField(blank=True)
    grant = models.ForeignKey(
        "policies.ExceptionGrant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "action"],
                condition=models.Q(status="pending"),
                name="one_pending_exception_request_per_project_action",
            )
        ]


class SubmissionReceipt(ImmutableMixin, PublicIdModel):
    version = models.OneToOneField(
        "projects.SubmissionVersion", on_delete=models.PROTECT, related_name="receipt"
    )
    token = models.TextField()
    issued_at = models.DateTimeField(auto_now_add=True)
