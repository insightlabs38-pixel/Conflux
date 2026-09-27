from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event
from stages.models import Stage


class FormDefinition(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="forms")
    stage = models.ForeignKey(
        Stage, null=True, blank=True, on_delete=models.SET_NULL, related_name="forms"
    )
    name = models.CharField(max_length=160)
    draft_schema = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_form_name_event")
        ]

    def clean(self):
        if self.stage_id and self.stage.event_id != self.event_id:
            raise ValidationError({"stage": "Stage must belong to the form's event."})


class FormVersion(PublicIdModel):
    definition = models.ForeignKey(
        FormDefinition, on_delete=models.PROTECT, related_name="versions"
    )
    number = models.PositiveIntegerField()
    schema = models.JSONField()
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["definition", "number"], name="unique_form_version")
        ]
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Published form versions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Published form versions are immutable.")
