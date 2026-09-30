"""What a destructive or high-impact operation would do, stated before it is done (PD-F001-B02).

A generic "Are you sure?" says nothing. This answers from the domain itself: for deletes it asks
Django's own deletion collector what would be removed, changed or protected (so the answer cannot
drift from what the endpoint really does), and for status changes it states the facts the platform
enforces. It never changes anything; the operation's own endpoint still validates, authorizes and
audits, and refuses exactly what `refusal` says.
"""

import copy

from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import ProtectedError, RestrictedError
from django.db.models.deletion import Collector
from django.utils import timezone
from evaluations.models import RubricVersion
from events.models import STATUS_FLOW, BasePrize, EventApplication, EventStatus, Track
from stages.graph import StageGraphError, validate_event_graph
from stages.models import Stage, StageTransition

from .readiness import compute_readiness
from .registry import SPECS

ACTIONS = (
    "event.open",
    "event.close",
    "event.archive",
    "event.delete",
    "stage.delete",
    "stage_transition.delete",
    "track.delete",
    "base_prize.delete",
)
STATUS_ACTIONS = {"event.open": "open", "event.close": "closed", "event.archive": "archived"}
_TARGETS = {
    "stage.delete": Stage,
    "stage_transition.delete": StageTransition,
    "track.delete": Track,
    "base_prize.delete": BasePrize,
}
# Records that exist only to hold the target's configuration are named for what they are.
_LABELS = {
    "rubricversion": "published rubric version",
    "evaluationplan": "judging plan",
    "stagetransition": "stage link",
    "eventregistrationsettings": "registration settings",
    "eligibilityrules": "eligibility rules",
    "eventprofile": "format record",
}
_PERMANENT = {RubricVersion}


class UnknownAction(ValueError):
    pass


def _label(model, count):
    name = _LABELS.get(model._meta.model_name, model._meta.verbose_name)
    return f"{count} {name}" + ("" if count == 1 else "s")


def _consequence(code, message, count=None):
    return {"code": code, "message": message, "count": count}


def _collect(instance):
    """(blockers, removed, changed) of deleting `instance`, as the deletion collector sees it."""
    collector = Collector(using=instance._state.db or "default")
    try:
        collector.collect([instance])
    except (ProtectedError, RestrictedError) as error:
        protected = list(getattr(error, "protected_objects", [])) or list(
            getattr(error, "restricted_objects", [])
        )
        counts = {}
        for obj in protected:
            counts[type(obj)] = counts.get(type(obj), 0) + 1
        blockers = []
        for model, count in counts.items():
            if model in _PERMANENT:
                blockers.append(
                    _consequence(
                        "published_rubric",
                        f"Its judging has {_label(model, count)}, which is permanent once "
                        "published and cannot be deleted.",
                        count,
                    )
                )
            else:
                blockers.append(
                    _consequence(
                        "protected",
                        f"{_label(model, count)} still depend on it and are protected.",
                        count,
                    )
                )
        return blockers, [], []

    counts = {}
    for model, rows in collector.data.items():
        counts[model] = counts.get(model, 0) + len(rows)
    for queryset in collector.fast_deletes:
        counts[queryset.model] = counts.get(queryset.model, 0) + queryset.count()
    removed = [
        _consequence("removed", f"{_label(model, count)} will be deleted.", count)
        for model, count in counts.items()
        if model is not type(instance) and count
    ]
    updates = {}
    for (field, _value), groups in collector.field_updates.items():
        for rows in groups:
            size = rows.count() if hasattr(rows, "count") and callable(rows.count) else len(rows)
            updates[field.model] = updates.get(field.model, 0) + size
    changed = [
        _consequence("updated", f"{_label(model, count)} will no longer be linked to it.", count)
        for model, count in updates.items()
        if count
    ]
    return [], removed, changed


def _graph_after_removing(transition):
    """Whether the stage graph is still valid if this link were gone (rolled back, never saved)."""

    class _Rollback(Exception):
        pass

    problem = None
    try:
        with transaction.atomic():
            event = transition.from_stage.event
            StageTransition.objects.filter(pk=transition.pk).delete()
            try:
                validate_event_graph(event)
            except StageGraphError as error:
                problem = "; ".join(error.messages)
            raise _Rollback
    except _Rollback:
        pass
    return problem


def _delete_preview(action, event, target):
    blockers, removed, changed = _collect(target)
    consequences = []
    if action == "stage_transition.delete":
        problem = _graph_after_removing(target)
        consequences.append(
            _consequence(
                "advancement",
                f"Participants can no longer be advanced from {target.from_stage.name} to "
                f"{target.to_stage.name}.",
            )
        )
        if problem:
            consequences.append(_consequence("graph_invalid", f"The stage flow breaks: {problem}"))
    if action == "stage.delete" and target.entries.exists():
        blockers.insert(
            0,
            _consequence(
                "has_participants",
                "A stage that has ever held a participant cannot be deleted.",
            ),
        )
    if action == "event.delete" and event.status != EventStatus.DRAFT:
        blockers.insert(0, _consequence("not_draft", "Only draft events can be deleted."))
    consequences += removed + changed
    if not consequences and not blockers:
        consequences.append(_consequence("isolated", "Nothing else depends on it."))
    return blockers, consequences


def _status_preview(action, event):
    goal = STATUS_ACTIONS[action]
    blockers, consequences = [], []
    if STATUS_FLOW.get(event.status) != goal:
        blockers.append(
            _consequence("invalid_transition", f"Invalid transition from {event.status} to {goal}.")
        )
    if goal == EventStatus.OPEN:
        if event.ends_at and event.ends_at <= timezone.now():
            blockers.append(
                _consequence("ends_in_the_past", "An event cannot open after its end date.")
            )
        # The endpoint runs this validation on the changed event; so does the preview.
        candidate = copy.copy(event)
        candidate.status = goal
        try:
            candidate.full_clean()
        except ModelValidationError as error:
            for message in error.messages:
                blockers.append(_consequence("invalid", message))
        consequences.append(
            _consequence(
                "visibility",
                "The event page goes live for anyone with the link."
                if event.is_public
                else "The event page stays private: Public event page is off.",
            )
        )
        items = [i for i in compute_readiness(event)["items"] if not i["passed"]]
        for item in items:
            consequences.append(
                _consequence(
                    f"unresolved:{item['id']}",
                    f"Still unresolved ({item['severity']}): {item['detail']}",
                )
            )
        if not items:
            consequences.append(_consequence("ready", "Nothing is unresolved."))
    if goal == EventStatus.CLOSED:
        pending = EventApplication.objects.filter(event=event, status="pending").count()
        consequences.append(
            _consequence(
                "pending_applications",
                f"{pending} application{'' if pending == 1 else 's'} still pending review.",
                pending,
            )
        )
    if goal == EventStatus.ARCHIVED:
        locked = sum(1 for spec in SPECS if spec.write)
        consequences.append(
            _consequence(
                "read_only",
                f"All {locked} editable settings become read-only, and so do tracks, prizes "
                "and modules.",
                locked,
            )
        )
    consequences.append(
        _consequence("forward_only", "Status only moves forward; it cannot be set back.")
    )
    return blockers, consequences


def _title(action, event, target):
    if action in STATUS_ACTIONS:
        return {
            "event.open": f"Open {event.name}",
            "event.close": f"Close {event.name}",
            "event.archive": f"Archive {event.name}",
        }[action]
    name = getattr(target, "name", None)
    if action == "event.delete":
        return f"Delete {event.name}"
    if action == "stage.delete":
        return f"Delete stage {name}"
    if action == "track.delete":
        return f"Delete track {name}"
    if action == "base_prize.delete":
        return f"Delete prize {name}"
    return f"Delete the link {target.from_stage.name} → {target.to_stage.name}"


def target_for(action, event, public_id):
    """The row an action applies to, scoped to the event (None when it targets the event)."""
    model = _TARGETS.get(action)
    if model is None:
        return None
    scope = {
        Stage: {"event": event},
        StageTransition: {"from_stage__event": event},
        Track: {"event": event},
        BasePrize: {"event": event},
    }[model]
    return model.objects.filter(public_id=public_id, **scope).first()


def preview(action, event, target=None):
    if action not in ACTIONS:
        raise UnknownAction(action)
    if action in STATUS_ACTIONS:
        blockers, consequences = _status_preview(action, event)
    else:
        subject = event if action == "event.delete" else target
        blockers, consequences = _delete_preview(action, event, subject)
    title = _title(action, event, target)
    reversible = action in ("stage_transition.delete",)
    return {
        "action": action,
        "title": title,
        "target": {"id": str(target.public_id), "name": getattr(target, "name", "")}
        if target is not None
        else None,
        "allowed": not blockers,
        "refusal": {"code": blockers[0]["code"], "message": blockers[0]["message"]}
        if blockers
        else None,
        "blockers": blockers,
        "consequences": consequences,
        "reversible": reversible,
        "severity": "medium" if reversible else "high",
        "confirm_label": title,
    }


def audit_snapshot(shown):
    """What the operation did, for its audit record: the consequences as they were when it ran."""
    return [
        {"code": c["code"], "count": c["count"]}
        for c in shown["consequences"]
        if c["code"] not in ("forward_only", "isolated")
    ]


def refusal_detail(shown):
    """The error body an endpoint returns when the preview says the operation is refused."""
    code, message = shown["refusal"]["code"], shown["refusal"]["message"]
    return {"status" if code == "not_draft" else "detail": message}
