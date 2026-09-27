from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event
from projects.models import Project
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


class FormResponse(PublicIdModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="form_responses")
    version = models.ForeignKey(FormVersion, on_delete=models.PROTECT, related_name="responses")
    updated_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="form_responses_updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "version"], name="unique_project_form_response"
            )
        ]

    def clean(self):
        if self.project.event_id != self.version.definition.event_id:
            raise ValidationError("Form and project must belong to the same event.")


class FormAnswer(PublicIdModel):
    response = models.ForeignKey(FormResponse, on_delete=models.CASCADE, related_name="answers")
    field_id = models.CharField(max_length=64)
    value = models.JSONField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["response", "field_id"], name="unique_form_answer_field"
            )
        ]

    def clean(self):
        from .validation import validate_answer

        field = next(
            (
                field
                for field in self.response.version.schema["fields"]
                if field["id"] == self.field_id
            ),
            None,
        )
        if field is None:
            raise ValidationError({"field_id": "Unknown field in this form version."})
        validate_answer(field, self.value)
