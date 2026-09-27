from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import transaction
from stages.models import Stage

from .models import FormDefinition, FormVersion


def validate_draft_schema(schema):
    if not isinstance(schema, dict) or not isinstance(schema.get("fields"), list):
        raise ValidationError({"schema": "Schema must contain a fields list."})
    ids = []
    for field in schema["fields"]:
        if not isinstance(field, dict) or not isinstance(field.get("id"), str) or not field["id"]:
            raise ValidationError({"schema": "Every field needs a nonempty string id."})
        ids.append(field["id"])
    if len(ids) != len(set(ids)):
        raise ValidationError({"schema": "Field ids must be unique."})


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
