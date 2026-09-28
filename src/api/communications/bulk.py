import hashlib
import json
import uuid
from datetime import timedelta

from audit.services import diff_snapshots, record_mutation, snapshot_fields
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from evaluations.assignment import activate
from evaluations.eligibility import eligible_projects
from evaluations.models import EvaluationPlan, PoolMembership
from events.models import Event, EventStatus, Track
from policies.models import TemporalGate
from projects.models import Project
from rest_framework.utils.encoders import JSONEncoder
from stages.advancement import Candidate, advance_stage
from stages.models import Stage, StageEntry

from .audiences import AUDIENCE_KINDS, resolve_audience
from .models import BulkReceipt
from .services import create_inbox_message

TOKEN_TTL = 600
MAX_EFFECTS = 1000
SALT = "communications.bulk.v1"


class StalePreview(Exception):
    pass


def _digest(value):
    raw = json.dumps(value, cls=JSONEncoder, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _targets(queryset, ids):
    rows = list(queryset.select_for_update().filter(public_id__in=ids).order_by("public_id"))
    if len(rows) != len(ids):
        raise ValidationError("One or more targets are unavailable in this event.")
    return rows


def _one(queryset, public_id):
    return _targets(queryset, [public_id])[0]


def _assign(event, actor, op):
    plan = _one(EvaluationPlan.objects.filter(stage__event=event), op["plan"])
    candidates = eligible_projects(plan).count()
    judges = PoolMembership.objects.filter(pool_id=plan.pool_id).count()
    if max(candidates, judges, candidates * judges) > MAX_EFFECTS:
        raise ValidationError("Assignment candidate/judge matrix exceeds the bulk impact limit.")
    before = (
        str(plan.active_assignment_version.public_id) if plan.active_assignment_version else None
    )
    version = activate(plan, coverage=op["coverage"])
    pairs = list(
        version.assignments.order_by("judge_id", "project_id").values_list("judge_id", "project_id")
    )
    if len(pairs) > MAX_EFFECTS:
        raise ValidationError("Assignment exceeds the bulk impact limit.")
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="assignment.activated",
        target=version,
        metadata=version.evidence,
    )
    return {
        "plan": str(plan.public_id),
        "before": before,
        "number": version.number,
        "pairs": pairs,
        "evidence": version.evidence,
    }, len(pairs)


def _advance(event, actor, op):
    stage = _one(Stage.objects.filter(event=event), op["stage"])
    target = _one(Stage.objects.filter(event=event), op["to_stage"])
    entries = _targets(
        StageEntry.objects.filter(stage=stage, exited_at__isnull=True), op["entries"]
    )
    candidates = [Candidate(e.subject_type, e.subject_id) for e in entries]
    advanced = advance_stage(stage, target, "everyone", candidates, actor=actor, params={})
    advanced.sort(key=lambda item: (item["subject_type"], item["subject_id"]))
    return {
        "stage": str(stage.public_id),
        "to_stage": str(target.public_id),
        "entries": [str(e.public_id) for e in entries],
        "advanced": advanced,
    }, len(advanced)


def _extend(event, actor, op):
    gates = _targets(TemporalGate.objects.filter(event=event), op["gates"])
    changes = []
    for gate in gates:
        if gate.closes_at is None:
            raise ValidationError("An unbounded gate cannot be extended.")
        before = snapshot_fields(gate, ["opens_at", "closes_at"])
        gate.closes_at += timedelta(seconds=op["seconds"])
        gate.full_clean()
        gate.save(update_fields=["closes_at"])
        diff = diff_snapshots(before, snapshot_fields(gate, ["opens_at", "closes_at"]))
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="temporal_gate.updated",
            target=gate,
            metadata={"changes": diff},
            event_type="temporal_gate.updated",
            payload={"event": str(event.public_id)},
        )
        changes.append({"gate": str(gate.public_id), "changes": diff})
    return {"changes": changes}, len(gates)


def _move(event, actor, op):
    track = _one(Track.objects.filter(event=event), op["track"])
    projects = _targets(Project.objects.filter(event=event), op["projects"])
    changes = []
    for project in projects:
        before = str(project.track.public_id) if project.track_id else None
        project.track = track
        project.full_clean()
        project.save(update_fields=["track", "updated_at"])
        change = {
            "project": str(project.public_id),
            "before": before,
            "after": str(track.public_id),
        }
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="project.track_moved",
            target=project,
            metadata=change,
        )
        changes.append(change)
    return {"changes": changes}, len(projects)


def _send(event, actor, op):
    params = op.get("audience_params", {})
    kind = AUDIENCE_KINDS.get(op["audience_kind"])
    if kind is None or params.keys() - set(kind.param_names):
        raise ValidationError("Unknown audience or audience parameters.")
    audience = resolve_audience(event, op["audience_kind"], params)
    recipients = list(
        audience.order_by("public_id").values_list("public_id", flat=True)[: MAX_EFFECTS + 1]
    )
    if len(recipients) > MAX_EFFECTS:
        raise ValidationError("Audience exceeds the bulk impact limit.")
    message = create_inbox_message(
        event=event,
        actor=actor,
        subject=op["subject"],
        body=op["body"],
        audience_kind=op["audience_kind"],
        audience_params=params,
    )
    actual = sorted(
        str(value) for value in message.recipients.values_list("user__public_id", flat=True)
    )
    if actual != sorted(str(value) for value in recipients):
        raise StalePreview("Audience changed during delivery; preview again.")
    return {"recipient_count": len(actual), "recipients": actual, "delivery": "inbox"}, len(actual)


def _execute(event, actor, operations):
    effects = []
    count = 0
    for op in operations:
        handler = {
            "assign": _assign,
            "advance": _advance,
            "extend": _extend,
            "move": _move,
            "send": _send,
        }[op["action"]]
        effect, impact = handler(event, actor, op)
        count += impact
        if count > MAX_EFFECTS:
            raise ValidationError("Batch exceeds the bulk impact limit.")
        effects.append({"action": op["action"], **effect})
    return json.loads(json.dumps(effects, cls=JSONEncoder))


def run_bulk(*, event, actor, operations, preview_token=None):
    request_digest = _digest(
        {"event": str(event.public_id), "actor": str(actor.public_id), "operations": operations}
    )
    claim = None
    if preview_token:
        try:
            claim = signing.loads(preview_token, salt=SALT, max_age=TOKEN_TTL)
        except signing.BadSignature as exc:
            raise StalePreview("Preview is invalid or expired; preview again.") from exc
        if claim.get("request") != request_digest:
            raise StalePreview("Preview does not match this actor, event or request.")

    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event.pk)
        if event.status == EventStatus.ARCHIVED:
            raise ValidationError("Archived events cannot run bulk operations.")
        token_digest = _digest(preview_token) if preview_token else None
        if token_digest:
            receipt = BulkReceipt.objects.filter(
                token_digest=token_digest, event=event, actor=actor
            ).first()
            if receipt:
                return receipt.result
        with transaction.atomic():
            # Every handler is DB-only: the preview savepoint must also roll back
            # domain/audit intent, and must never initiate external delivery.
            effects = _execute(event, actor, operations)
            if not claim:
                transaction.set_rollback(True)
            elif claim["effects"] != _digest(effects):
                raise StalePreview("Preview effects changed; preview again.")
        if not claim:
            token = signing.dumps(
                {
                    "request": request_digest,
                    "effects": _digest(effects),
                    "nonce": str(uuid.uuid4()),
                },
                salt=SALT,
            )
            return {
                "applied": False,
                "effects": effects,
                "preview_token": token,
                "expires_in": TOKEN_TTL,
            }
        result = {"applied": True, "effects": effects}
        receipt = BulkReceipt.objects.create(
            event=event, actor=actor, token_digest=token_digest, result=result
        )
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="operations.bulk_applied",
            target=receipt,
            metadata={"event": str(event.public_id), "effects": effects},
        )
        return result
