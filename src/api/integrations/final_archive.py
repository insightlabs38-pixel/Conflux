"""Canonical v3 snapshots restored atomically into fresh, private event-owned rows."""

import hashlib
import json
import uuid
from copy import deepcopy

from accounts.models import User
from artifacts.models import STORED_KINDS
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import JSONField
from events.models import Event

from .final_archive_json import remap_json
from .final_archive_schema import TABLES, V2_TABLES
from .models import ArchiveRestoration

EVENT_FIELDS = (
    "name slug description timezone starts_at ends_at status is_public created_at updated_at"
).split()
DEFERRED = {
    ("projects.submission", "current_version"),
    ("evaluations.evaluationplan", "active_assignment_version"),
    ("evaluations.evaluationplan", "published_normalization_run"),
    ("evaluations.evaluationplan", "published_pairwise_run"),
    ("evaluations.evaluationplan", "hybrid_source"),
}


def canonical_bytes(value):
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    except (TypeError, ValueError) as exc:
        raise ValidationError("Archive must contain finite JSON values.") from exc


def _error(message):
    raise ValidationError({"archive": message})


def _uuid(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            _error("Archive references must be canonical UUID strings.")
        return value
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError("Archive references must be UUID strings.") from exc


def _fields(model, names):
    return [model._meta.get_field(name) for name in names.split()]


def _scalar(field, obj):
    value = getattr(obj, field.name)
    if value is None or isinstance(field, JSONField):
        return deepcopy(value)
    if field.get_internal_type() in {"DateTimeField", "DateField", "DecimalField", "UUIDField"}:
        return field.value_to_string(obj)
    return value


def build_final_archive(event):
    models = {label: apps.get_model(label) for label in TABLES}
    objects = {
        label: list(
            model.objects.filter(**{TABLES[label][0]: event}).order_by(
                *(("position", "pk") if label == "awards.awardresource" else ("public_id",))
            )
        )
        for label, model in models.items()
    }
    restoration = ArchiveRestoration.objects.filter(event=event).first()
    origin = {
        (label, new): old
        for label, mapping in (restoration.identity_map if restoration else {}).items()
        for old, new in mapping.items()
    }
    users = {}

    def reference(obj):
        label = obj._meta.label_lower
        ref = origin.get((label, str(obj.public_id)), str(obj.public_id))
        if label == "accounts.user":
            users[ref] = {"ref": ref, "username": obj.username}
        return ref

    by_pk = {(label, str(obj.pk)): obj for label, rows in objects.items() for obj in rows}
    by_public = {
        (label, str(obj.public_id)): obj for label, rows in objects.items() for obj in rows
    }
    by_public[("events.event", str(event.public_id))] = event

    def lookup(label, value, *, primary=False):
        if label == "accounts.user":
            try:
                return User.objects.get(**{"pk" if primary else "public_id": value})
            except (User.DoesNotExist, ValueError) as exc:
                raise ValidationError("Evidence references an unknown user.") from exc
        found = (by_pk if primary else by_public).get((label, str(value)))
        if found is None:
            _error(f"Evidence reference {label}:{value} is outside this event.")
        return found

    def public(label, value):
        return reference(lookup(label, value))

    def pk(label, value):
        return reference(lookup(label, value, primary=True))

    tables = {}
    for label, rows in objects.items():
        table = []
        for obj in rows:
            data = {}
            for field in _fields(models[label], TABLES[label][1]):
                value = getattr(obj, field.name)
                if field.is_relation:
                    if value is not None:
                        target = value._meta.label_lower
                        if target != "accounts.user" and target != "events.event":
                            lookup(target, value.public_id)
                        elif target == "events.event" and value.pk != event.pk:
                            _error("Cross-event reference in final archive.")
                    data[field.name] = reference(value) if value is not None else None
                else:
                    data[field.name] = (
                        remap_json(label, field.name, _scalar(field, obj), pk=pk, public=public)
                        if isinstance(field, JSONField)
                        else _scalar(field, obj)
                    )
            if label == "evaluations.pairwisecomparison" and data["project_a"] > data["project_b"]:
                # Archive order uses portable refs, independent of database insertion order.
                data["project_a"], data["project_b"] = data["project_b"], data["project_a"]
            if label == "stages.stageentry":
                subject_label = {"team": "participation.team", "user": "accounts.user"}.get(
                    obj.subject_type
                )
                if subject_label is None:
                    _error("Unsupported stage subject type.")
                data["subject_id"] = public(subject_label, obj.subject_id)
            if label == "projects.submissionversion":
                data["digest"] = hashlib.sha256(
                    json.dumps(data["snapshot"], sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
            m2m = {}
            for name in TABLES[label][2].split():
                targets = list(getattr(obj, name).all())
                for target in targets:
                    lookup(target._meta.label_lower, target.public_id)
                m2m[name] = sorted(reference(target) for target in targets)
            table.append({"ref": reference(obj), "fields": data, "m2m": m2m})
        tables[label] = sorted(
            table,
            key=(
                (lambda row: (row["fields"]["award"], row["fields"]["position"]))
                if label == "awards.awardresource"
                else (lambda row: row["ref"])
            ),
        )
    provenance = deepcopy(restoration.source_archive.get("provenance", []) if restoration else [])
    if restoration:
        provenance.append(
            {
                "source_sha256": restoration.source_sha256,
                "source_event_ref": restoration.source_archive["event"]["ref"],
                "source_format_version": restoration.source_archive["format_version"],
            }
        )
    archive = {
        "format_version": 3,
        "mode": "final",
        "event": {
            "ref": reference(event),
            "fields": {name: _scalar(Event._meta.get_field(name), event) for name in EVENT_FIELDS},
        },
        "users": sorted(users.values(), key=lambda row: row["ref"]),
        "tables": tables,
        "provenance": provenance,
    }
    canonical_bytes(archive)
    return archive


def _validate_shape(archive):
    canonical_bytes(archive)
    if not isinstance(archive, dict) or set(archive) != {
        "format_version",
        "mode",
        "event",
        "users",
        "tables",
        "provenance",
    }:
        _error("A final archive needs exactly the final-archive contract keys.")
    if (
        type(archive["format_version"]) is not int
        or archive["format_version"] not in (2, 3)
        or archive["mode"] != "final"
    ):
        _error("Expected format_version 2 or 3 and mode final.")
    if not isinstance(archive["tables"], dict) or set(archive["tables"]) != set(
        V2_TABLES if archive["format_version"] == 2 else TABLES
    ):
        _error("Final archives require every known table, including empty tables.")
    if not isinstance(archive["event"], dict) or set(archive["event"]) != {"ref", "fields"}:
        _error("Invalid event envelope.")
    if not isinstance(archive["event"]["fields"], dict) or set(archive["event"]["fields"]) != set(
        EVENT_FIELDS
    ):
        _error("Invalid event fields.")
    _uuid(archive["event"]["ref"])
    if not isinstance(archive["users"], list) or not isinstance(archive["provenance"], list):
        _error("Users and provenance must be lists.")
    for item in archive["provenance"]:
        if not isinstance(item, dict) or set(item) != {
            "source_sha256",
            "source_event_ref",
            "source_format_version",
        }:
            _error("Invalid provenance entry.")
        _uuid(item["source_event_ref"])
        if (
            type(item["source_format_version"]) is not int
            or item["source_format_version"] not in (2, 3)
            or not isinstance(item["source_sha256"], str)
            or len(item["source_sha256"]) != 64
        ):
            _error("Invalid provenance version/checksum.")
    for label, rows in archive["tables"].items():
        if not isinstance(rows, list):
            _error(f"{label} must be a list.")
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"ref", "fields", "m2m"}:
                _error(f"Invalid {label} row.")
            _uuid(row["ref"])
            if not isinstance(row["fields"], dict) or set(row["fields"]) != set(
                TABLES[label][1].split()
            ):
                _error(f"Invalid {label} fields.")
            if not isinstance(row["m2m"], dict) or set(row["m2m"]) != set(TABLES[label][2].split()):
                _error(f"Invalid {label} many-to-many fields.")


@transaction.atomic
def restore_final_archive(*, workspace, archive, name, slug):
    _validate_shape(archive)
    digest = hashlib.sha256(canonical_bytes(archive)).hexdigest()
    event_data = archive["event"]["fields"]
    event = Event(
        workspace=workspace,
        name=name,
        slug=slug,
        status="draft",
        is_public=False,
        **{
            key: Event._meta.get_field(key).to_python(event_data[key])
            for key in ("description", "timezone", "starts_at", "ends_at")
        },
    )
    event.full_clean()
    event.save()
    refs = {("events.event", archive["event"]["ref"]): event}
    for user in archive["users"]:
        if not isinstance(user, dict) or set(user) != {"ref", "username"}:
            _error("Invalid archived user.")
        ref = _uuid(user["ref"])
        if ("accounts.user", ref) in refs:
            _error("Duplicate user reference.")
        try:
            refs[("accounts.user", ref)] = User.objects.get(username=user["username"])
        except (User.DoesNotExist, TypeError) as exc:
            raise ValidationError(
                "All archived users must already exist by exact username."
            ) from exc
    if len({obj.pk for (label, _), obj in refs.items() if label == "accounts.user"}) != len(
        archive["users"]
    ):
        _error("Multiple archived users cannot resolve to one identity.")

    rows = {}
    for label, table in archive["tables"].items():
        model = apps.get_model(label)
        for row in table:
            key = (label, row["ref"])
            if key in refs:
                _error(f"Duplicate {label} reference.")
            refs[key] = model()
            rows[key] = row

    def resolve(label, value):
        try:
            return refs[(label, value)]
        except (KeyError, TypeError) as exc:
            raise ValidationError(f"Unknown {label} reference: {value!r}.") from exc

    def public(label, value):
        return str(resolve(label, value).public_id)

    def pk(label, value):
        obj = resolve(label, value)
        if not obj.pk:
            _error("Evidence depends on a row that has not been restored.")
        return obj.pk

    pending = dict(rows)
    timestamps = {}
    try:
        while pending:
            progressed = False
            for key, row in list(pending.items()):
                label, _ = key
                obj = refs[key]
                fields = _fields(type(obj), TABLES[label][1])
                dependencies = [
                    resolve(field.remote_field.model._meta.label_lower, row["fields"][field.name])
                    for field in fields
                    if field.is_relation
                    and row["fields"][field.name] is not None
                    and (label, field.name) not in DEFERRED
                ]
                if any(target.pk is None for target in dependencies):
                    continue
                times = {}
                for field in fields:
                    value = row["fields"][field.name]
                    if field.is_relation:
                        value = (
                            None
                            if (label, field.name) in DEFERRED or value is None
                            else resolve(field.remote_field.model._meta.label_lower, value)
                        )
                    elif isinstance(field, JSONField):
                        value = remap_json(label, field.name, value, pk=pk, public=public)
                    else:
                        value = field.to_python(value)
                    if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                        times[field.name] = value
                    setattr(obj, field.name, value)
                if label == "stages.stageentry":
                    subject = {"team": "participation.team", "user": "accounts.user"}.get(
                        obj.subject_type
                    )
                    if subject is None or obj.subject_type != obj.stage.expected_subject_type():
                        _error("Invalid stage subject type.")
                    obj.subject_id = public(subject, row["fields"]["subject_id"])
                if label == "artifacts.artifact" and obj.kind in STORED_KINDS:
                    # Historical storage metadata cannot prove that a new object exists.
                    obj.status, obj.object_key = "pending", ""
                if label == "projects.submissionversion":
                    obj.digest = hashlib.sha256(
                        json.dumps(obj.snapshot, sort_keys=True, separators=(",", ":")).encode()
                    ).hexdigest()
                if (
                    label == "evaluations.pairwisecomparison"
                    and obj.project_a_id > obj.project_b_id
                ):
                    # Fresh primary keys may reverse the source comparison's canonical order.
                    obj.project_a, obj.project_b = obj.project_b, obj.project_a
                obj.save(force_insert=True)
                timestamps[key] = times
                del pending[key]
                progressed = True
            if not progressed:
                _error("Final archive contains an unsupported dependency cycle.")
        for key, row in rows.items():
            label, _ = key
            obj = refs[key]
            updates = timestamps[key]
            for deferred_label, field_name in DEFERRED:
                if label == deferred_label:
                    field = obj._meta.get_field(field_name)
                    ref = row["fields"][field_name]
                    target = (
                        resolve(field.remote_field.model._meta.label_lower, ref) if ref else None
                    )
                    setattr(obj, field_name, target)
                    updates[field.attname] = target.pk if target else None
            # Patch only fresh rows before validation/commit; never edit existing history.
            if updates:
                type(obj).objects.filter(pk=obj.pk).update(**updates)
            for field_name, values in row["m2m"].items():
                if not isinstance(values, list) or len(values) != len(set(values)):
                    _error("Many-to-many references must be unique lists.")
                field = obj._meta.get_field(field_name)
                getattr(obj, field_name).set(
                    resolve(field.remote_field.model._meta.label_lower, ref) for ref in values
                )
        for key in rows:
            obj = refs[key]
            obj.refresh_from_db()
            obj.full_clean()
            _validate_links(obj)
        identity_map = {}
        for (label, ref), obj in refs.items():
            identity_map.setdefault(label, {})[ref] = str(obj.public_id)
        record = ArchiveRestoration(
            event=event,
            source_sha256=digest,
            source_archive=deepcopy(archive),
            identity_map=identity_map,
        )
        record.full_clean()
        record.save()
    except (IntegrityError, ValueError, TypeError, KeyError) as exc:
        raise ValidationError("Invalid final archive; restoration was rolled back.") from exc
    return event


def _validate_links(obj):
    label = obj._meta.label_lower
    if label == "evaluations.evaluationplan":
        for name in (
            "active_assignment_version",
            "published_normalization_run",
            "published_pairwise_run",
        ):
            target = getattr(obj, name)
            if target is not None and target.plan_id != obj.pk:
                _error(f"{name} belongs to a different plan.")
        if obj.published_pairwise_run_id and obj.mode != "pairwise":
            _error("Pairwise results require a pairwise plan.")
        if obj.published_normalization_run_id and obj.mode != "rubric":
            _error("Normalization results require a rubric plan.")
    if label == "awards.awardwinner":
        if obj.project.event_id != obj.award.event_id:
            _error("Winner project belongs to a different event.")
    if (
        label == "evaluations.assignment"
        and obj.project.event_id != obj.version.plan.stage.event_id
    ):
        _error("Assigned project belongs to a different event.")
