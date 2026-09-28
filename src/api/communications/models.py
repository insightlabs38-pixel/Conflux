from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event


class EventQuestion(PublicIdModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="questions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    question = models.CharField(max_length=2000)
    answer = models.CharField(max_length=4000, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["event", "status", "created_at"])]


class ModerationReview(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="moderation_reviews")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=16)
    source_key = models.CharField(max_length=64)
    evidence_digest = models.CharField(max_length=64)
    evidence = models.JSONField()
    disposition = models.CharField(max_length=16)
    note = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["event", "kind", "source_key", "created_at"])]


class BulkReceipt(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bulk_receipts")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    token_digest = models.CharField(max_length=64, unique=True)
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class Message(PublicIdModel):
    """One organizer broadcast to a dynamically-resolved audience (OPS-002/
    OPS-003). The audience is never stored as a frozen recipient list at
    compose time -- `audience_kind`/`audience_params` are kept so the
    message's *intent* stays legible, but who actually received it is the
    `MessageRecipient` rows created at send time, which is the one
    trustworthy record of "who got this".
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="messages")
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_messages"
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    audience_kind = models.CharField(max_length=40)
    audience_params = models.JSONField(default=dict, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)
    email_failure_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def clean(self):
        if not self.subject.strip():
            raise ValidationError({"subject": "Subject cannot be empty."})
        if not self.body.strip():
            raise ValidationError({"body": "Body cannot be empty."})


class MessageRecipient(PublicIdModel):
    """One resolved recipient of a Message: the durable in-app inbox entry.
    Email delivery is a best-effort side channel recorded per-row
    (`email_sent_at`/`email_error`) -- a failed or unconfigured email
    transport never prevents the in-app copy from existing, which is what
    makes in-app delivery the offline-compatible baseline (OPS-003).
    """

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="recipients")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages"
    )
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_error = models.CharField(max_length=300, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user"], name="unique_message_recipient")
        ]
        ordering = ["-message__created_at", "-id"]


class ReminderKind(models.TextChoices):
    DEADLINE = "deadline", "Submission deadline"
    JUDGING = "judging", "Judging"
    VOTING = "voting", "Voting"


class Reminder(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reminders")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_reminders"
    )
    kind = models.CharField(max_length=12, choices=ReminderKind.choices)
    due_at = models.DateTimeField()
    audience_kind = models.CharField(max_length=40)
    audience_params = models.JSONField(default=dict, blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_message = models.OneToOneField(
        Message, null=True, blank=True, on_delete=models.PROTECT, related_name="reminder"
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    retry_after = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at", "id"]

    def clean(self):
        if not self.subject.strip():
            raise ValidationError({"subject": "Subject cannot be empty."})
        if not self.body.strip():
            raise ValidationError({"body": "Body cannot be empty."})
