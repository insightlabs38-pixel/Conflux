import re
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.dateparse import parse_date, parse_datetime

FIELD_TYPES = {
    "text",
    "rich_text",
    "number",
    "select",
    "multi_select",
    "boolean",
    "url",
    "date",
    "datetime",
    "artifact",
}
FIELD_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
SCOPES = {"public", "participant", "judge", "organizer"}


def field_scopes(field):
    return set(field.get("visible_to", ["participant", "judge", "organizer"]))


def field_visible(field, scope, answers):
    scopes = field_scopes(field)
    if scope not in scopes and "public" not in scopes:
        return False
    condition = field.get("visible_if")
    return condition is None or answers.get(condition["field"]) == condition["equals"]


def field_required(field, answers):
    condition = field.get("required_if")
    return field.get("required", False) or (
        condition is not None and answers.get(condition["field"]) == condition["equals"]
    )


def validate_schema(schema):
    if not isinstance(schema, dict) or not isinstance(schema.get("fields"), list):
        raise ValidationError({"schema": "Schema must contain a fields list."})
    fields = schema["fields"]
    if len(fields) > 100:
        raise ValidationError({"schema": "A form may have at most 100 fields."})
    seen = set()
    prior = {}
    for field in fields:
        if not isinstance(field, dict):
            raise ValidationError({"schema": "Every field must be an object."})
        field_id = field.get("id")
        if not isinstance(field_id, str) or not FIELD_ID.fullmatch(field_id):
            raise ValidationError({"schema": "Field ids must be lowercase identifiers."})
        if field_id in seen:
            raise ValidationError({"schema": "Field ids must be unique."})
        seen.add(field_id)
        if field.get("type") not in FIELD_TYPES:
            raise ValidationError({"schema": f"Field {field_id} has an unsupported type."})
        if not isinstance(field.get("label"), str) or not field["label"].strip():
            raise ValidationError({"schema": f"Field {field_id} needs a label."})
        if not isinstance(field.get("required", False), bool):
            raise ValidationError({"schema": f"Field {field_id} required must be boolean."})
        if field["type"] in {"select", "multi_select"}:
            options = field.get("options")
            if (
                not isinstance(options, list)
                or not options
                or any(not isinstance(x, str) or not x for x in options)
                or len(options) != len(set(options))
            ):
                raise ValidationError(
                    {"schema": f"Field {field_id} needs unique nonempty options."}
                )
        scopes = field.get("visible_to", ["participant", "judge", "organizer"])
        if (
            not isinstance(scopes, list)
            or not scopes
            or any(not isinstance(scope, str) or scope not in SCOPES for scope in scopes)
            or len(scopes) != len(set(scopes))
        ):
            raise ValidationError({"schema": f"Field {field_id} has invalid visibility scopes."})
        for key in ("visible_if", "required_if"):
            condition = field.get(key)
            if condition is None:
                continue
            if (
                not isinstance(condition, dict)
                or set(condition) != {"field", "equals"}
                or not isinstance(condition.get("field"), str)
                or condition["field"] not in prior
            ):
                raise ValidationError(
                    {"schema": f"Field {field_id} has an invalid {key} condition."}
                )
            controller = prior[condition["field"]]
            if (
                controller["type"] not in {"select", "boolean"}
                or (
                    controller["type"] == "select"
                    and condition["equals"] not in controller["options"]
                )
                or (controller["type"] == "boolean" and not isinstance(condition["equals"], bool))
            ):
                raise ValidationError(
                    {"schema": f"Field {field_id} has an incompatible {key} condition."}
                )
            controller_scopes = field_scopes(controller)
            dependent_scopes = field_scopes(field)
            if "public" not in controller_scopes and (
                "public" in dependent_scopes or not dependent_scopes <= controller_scopes
            ):
                raise ValidationError(
                    {"schema": f"Field {field_id} condition refers to a less visible field."}
                )
        prior[field_id] = field


def validate_response_answers(schema, answers, scope):
    if not isinstance(answers, dict):
        raise ValidationError("Answers must be an object keyed by field id.")
    fields = {field["id"]: field for field in schema["fields"]}
    if set(answers) - set(fields):
        raise ValidationError("Answers contain an unknown field.")
    for field in schema["fields"]:
        field_id = field["id"]
        if not field_visible(field, scope, answers):
            if field_id in answers:
                raise ValidationError(f"{field_id} is not visible in this response.")
            continue
        effective = {**field, "required": field_required(field, answers)}
        validate_answer(effective, answers.get(field_id))


def validate_answer(field, value):
    kind = field["type"]
    if value is None or value == "" or value == []:
        if field.get("required", False):
            raise ValidationError(f"{field['id']} is required.")
        return
    if kind in {"text", "rich_text", "url", "date", "datetime", "artifact"} and not isinstance(
        value, str
    ):
        raise ValidationError(f"{field['id']} must be text.")
    if kind in {"text", "rich_text"} and len(value) > (50000 if kind == "rich_text" else 5000):
        raise ValidationError(f"{field['id']} is too long.")
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValidationError(f"{field['id']} must be a number.")
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValidationError(f"{field['id']} must be a number.") from exc
        if not number.is_finite():
            raise ValidationError(f"{field['id']} must be finite.")
    if kind == "boolean" and not isinstance(value, bool):
        raise ValidationError(f"{field['id']} must be true or false.")
    if kind == "select" and value not in field["options"]:
        raise ValidationError(f"{field['id']} must match an option.")
    if kind == "multi_select" and (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or len(value) != len(set(value))
        or any(item not in field["options"] for item in value)
    ):
        raise ValidationError(f"{field['id']} must contain unique listed options.")
    if kind == "url":
        URLValidator(schemes=["http", "https"])(value)
    if kind == "date":
        try:
            parsed = parse_date(value)
        except ValueError:
            parsed = None
        if parsed is None:
            raise ValidationError(f"{field['id']} must be an ISO date.")
    if kind == "datetime":
        try:
            parsed = parse_datetime(value)
        except ValueError:
            parsed = None
        if parsed is None:
            raise ValidationError(f"{field['id']} must be an ISO datetime.")
    if kind == "artifact":
        try:
            UUID(value)
        except (ValueError, AttributeError) as exc:
            raise ValidationError(f"{field['id']} must be an artifact id.") from exc
