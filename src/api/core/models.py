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
