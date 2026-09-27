from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import transaction
from projects.models import Project
from stages.models import Stage

from .models import FormAnswer, FormDefinition, FormResponse, FormVersion
from .validation import validate_answer, validate_schema


def validate_draft_schema(schema):
    validate_schema(schema)


@transaction.atomic
def create_form(event, name, *, stage=None):
    if stage is not None and (not isinstance(stage, Stage) or stage.event_id != event.id):
        raise ValidationError({"stage": "Stage must belong to the form's event."})
    definition = FormDefinition(event=event, stage=stage, name=name, draft_schema={"fields": []})
    definition.full_clean()
    definition.save()
    return definition


@transaction.atomic
def save_draft(definition, schema):
    validate_draft_schema(schema)
    definition.draft_schema = deepcopy(schema)
    definition.full_clean()
    definition.save(update_fields=["draft_schema", "updated_at"])
    return definition


@transaction.atomic
def publish_form(definition):
    definition = FormDefinition.objects.select_for_update().get(pk=definition.pk)
    validate_draft_schema(definition.draft_schema)
    latest = definition.versions.order_by("-number").first()
    number = 1 if latest is None else latest.number + 1
    version = FormVersion(
        definition=definition, number=number, schema=deepcopy(definition.draft_schema)
    )
    version.full_clean()
    version.save()
    return version


@transaction.atomic
def save_response(project, version, actor, answers):
    Project.objects.select_for_update().get(pk=project.pk)
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only project members can edit its form response.")
    if version.definition.event_id != project.event_id:
        raise ValidationError("Form and project must belong to the same event.")
    if not isinstance(answers, dict):
        raise ValidationError("Answers must be an object keyed by field id.")
    fields = {field["id"]: field for field in version.schema["fields"]}
    if set(answers) - set(fields):
        raise ValidationError("Answers contain an unknown field.")
    for field_id, field in fields.items():
        validate_answer(field, answers.get(field_id))
    response, _ = FormResponse.objects.select_for_update().get_or_create(
        project=project, version=version, defaults={"updated_by": actor}
    )
    response.updated_by = actor
    response.full_clean()
    response.save(update_fields=["updated_by", "updated_at"])
    response.answers.all().delete()
    for field_id, value in answers.items():
        answer = FormAnswer(response=response, field_id=field_id, value=value)
        answer.full_clean()
        answer.save()
    return response
