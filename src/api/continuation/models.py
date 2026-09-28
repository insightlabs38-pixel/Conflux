"""PVS15: what a project does after its event. Deliberately narrow -- one profile
per project plus a short append-only log of updates. It is not a project-hosting,
messaging or fundraising surface: no comments, no contact details, no money.
"""

from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

MAX_UPDATES_PER_PROJECT = 20
SEEKING_CHOICES = ("contributors", "mentors", "users", "feedback", "partners")


class ProjectContinuation(PublicIdModel):
    project = models.OneToOneField(
        "projects.Project", on_delete=models.CASCADE, related_name="continuation"
    )
    summary = models.CharField(max_length=1000)
    url = models.URLField(blank=True)
    seeking = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=False)
    hidden_at = models.DateTimeField(null=True, blank=True)
    hidden_reason = models.CharField(max_length=300, blank=True)
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ContinuationUpdate(PublicIdModel):
    continuation = models.ForeignKey(
        ProjectContinuation, on_delete=models.CASCADE, related_name="updates"
    )
    body = models.CharField(max_length=1000)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Continuation updates are append-only.")
        super().save(*args, **kwargs)
