import uuid

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
