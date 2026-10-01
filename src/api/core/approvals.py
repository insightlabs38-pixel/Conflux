"""Approval gates: a second person confirms one exact operation before it runs (PD-F002-B01-T06).

An approval only gates an operation whose effect is unchanged. It never computes a score, a
winner, a permission or a deadline, and a gate is **off by default**: with no gate enabled for the
event the operation behaves exactly as it always did.

A domain registers a policy (`register_policy`) and calls `require_approval` inside the
operation's own transaction, just before the effect:

    approvals.require_approval(event=, actor=, action="message_send", payload={...},
                               summary=["Send ... to 120 people"])

- Gate off: returns None, nothing changes.
- Gate on, a matching approved request (same action, same digest of the payload, not expired):
  it is consumed (`executed`) in the operation's transaction, so a rollback un-consumes it, and the
  operation proceeds. One approval is spent once.
- Otherwise `ApprovalRequired` is raised and the operation rolls back. The view answers with
  `exc.respond(actor)`, which (outside the failed transaction) opens or finds the pending request
  and returns 409 `{"code": "approval_required", "approval": {...}}`.
- `dry_run()` is for previews: nothing is raised, the need is collected for the preview to show.

Lifecycle (`TRANSITIONS`, always under a row lock):

    pending -> approved | rejected | cancelled | expired
    approved -> executed | cancelled | expired

The digest binds an approval to the content approvers read in `summary`: a changed subject,
body or audience is a different operation and needs a new request. The requester cannot approve
their own request unless the policy says so. Expiry is enforced when an approval is consumed or
decided and by a sweep. Every transition is audited.
"""

import contextvars
import hashlib
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta

from audit.services import record_mutation
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from .authz import has_any_role
from .models import ApprovalDecision, ApprovalGate, ApprovalRequest

MAX_SUMMARY_LINES = 10
MAX_SUMMARY_CHARS = 300
MAX_NOTE = 500

S = ApprovalRequest.Status
TRANSITIONS = {
    S.PENDING: {S.APPROVED, S.REJECTED, S.CANCELLED, S.EXPIRED},
    S.APPROVED: {S.EXECUTED, S.CANCELLED, S.EXPIRED},
    S.REJECTED: set(),
    S.CANCELLED: set(),
    S.EXPIRED: set(),
    S.EXECUTED: set(),
}
TERMINAL = frozenset(status for status, targets in TRANSITIONS.items() if not targets)


class ApprovalStateError(Exception):
    """The request is not in a state that allows this (already decided, expired, ...)."""


@dataclass(frozen=True)
class ApprovalPolicy:
    """What may be gated and who decides.

    `deciders` are workspace roles. `min_approvals` approvals are needed; one rejection ends the
    request. `ttl` is how long a request, and an approval nobody used, stays valid.
    """

    key: str
    label: str
    description: str
    deciders: tuple
    min_approvals: int = 1
    requester_may_approve: bool = False
    ttl: timedelta = timedelta(hours=72)


POLICIES: dict[str, ApprovalPolicy] = {}


def register_policy(policy: ApprovalPolicy):
    """Add a policy once; a different registration under a taken key is a bug."""
    if policy.key in POLICIES and POLICIES[policy.key] != policy:
        raise ValueError(f"Approval policy {policy.key!r} is already registered")
    if policy.min_approvals < 1 or not policy.deciders:
        raise ValueError("A policy needs at least one approval and one deciding role")
    POLICIES[policy.key] = policy
    return policy


def digest_of(action, subject, payload):
    raw = json.dumps(
        {"action": action, "subject": list(subject), "payload": payload},
        cls=JSONEncoder,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def gate_enabled(event, action):
    return ApprovalGate.objects.filter(event=event, action=action, enabled=True).exists()


def set_gate(*, event, actor, action, enabled):
    """Turn a gate on or off for the event; audited with before and after."""
    if action not in POLICIES:
        raise ValidationError({"action": ["Unknown operation."]})
    with transaction.atomic():
        gate, _ = ApprovalGate.objects.select_for_update(of=("self",)).get_or_create(
            event=event, action=action
        )
        before = gate.enabled
        if before != enabled:
            gate.enabled = enabled
            gate.updated_by = actor
            gate.save(update_fields=["enabled", "updated_by", "updated_at"])
            record_mutation(
                actor=actor,
                workspace=event.workspace,
                action="approval.gate_changed",
                target=event,
                metadata={"operation": action, "before": before, "after": enabled},
            )
    return gate


_dry_run = contextvars.ContextVar("approvals_dry_run", default=None)


@contextmanager
def dry_run():
    """Inside a preview: a needed approval is collected instead of raised."""
    needed = []
    token = _dry_run.set(needed)
    try:
        yield needed
    finally:
        _dry_run.reset(token)


def _clean_summary(lines):
    return [str(line)[:MAX_SUMMARY_CHARS] for line in list(lines)[:MAX_SUMMARY_LINES]]


class ApprovalRequired(Exception):
    """The operation needs an approval it does not have; carries what to ask approvers."""

    def __init__(self, *, event, action, subject, digest, summary):
        super().__init__(f"{action} needs approval")
        self.event = event
        self.action = action
        self.subject = subject
        self.digest = digest
        self.summary = summary

    def respond(self, actor):
        """Open (or find) the pending request and build the 409 answer. Call outside the
        transaction that was rolled back."""
        request, _ = open_request(
            event=self.event,
            actor=actor,
            action=self.action,
            subject=self.subject,
            digest=self.digest,
            summary=self.summary,
        )
        policy = POLICIES[self.action]
        return Response(
            {
                "code": "approval_required",
                "detail": f"{policy.label} needs approval from another person first.",
                "approval": describe(request, actor),
            },
            status=409,
        )


def require_approval(*, event, actor, action, payload, summary, subject=("", "")):
    """Gate point; see the module docstring. Returns the consumed request, or None when off."""
    policy = POLICIES.get(action)
    if policy is None:
        raise ValueError(f"No approval policy registered for {action!r}")
    if not gate_enabled(event, action):
        return None
    digest = digest_of(action, subject, payload)
    summary = _clean_summary(summary)
    collected = _dry_run.get()
    if collected is not None:
        collected.append({"action": action, "label": policy.label, "summary": summary})
        return None
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("require_approval must run inside the operation's transaction")
    now = timezone.now()
    approved = (
        ApprovalRequest.objects.select_for_update(of=("self",))
        .filter(event=event, action=action, digest=digest, status=S.APPROVED, expires_at__gt=now)
        .order_by("created_at")
        .first()
    )
    if approved is None:
        raise ApprovalRequired(
            event=event, action=action, subject=subject, digest=digest, summary=summary
        )
    approved.status = S.EXECUTED
    approved.executed_at = approved.closed_at = now
    approved.save(update_fields=["status", "executed_at", "closed_at"])
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="approval.executed",
        target=approved,
        metadata={"operation": action},
    )
    return approved


def open_request(*, event, actor, action, subject, digest, summary):
    """The pending request for this exact operation; a second ask returns the first."""
    policy = POLICIES[action]
    with transaction.atomic():
        pending = (
            ApprovalRequest.objects.select_for_update(of=("self",))
            .filter(event=event, action=action, digest=digest, status=S.PENDING)
            .first()
        )
        if pending and pending.expires_at > timezone.now():
            return pending, False
        if pending:
            _close(pending, S.EXPIRED, actor=None)
        try:
            with transaction.atomic():
                request = ApprovalRequest.objects.create(
                    workspace=event.workspace,
                    event=event,
                    action=action,
                    subject_type=subject[0],
                    subject_id=str(subject[1]),
                    summary=summary,
                    digest=digest,
                    requested_by=actor,
                    required_approvals=policy.min_approvals,
                    expires_at=timezone.now() + policy.ttl,
                )
        except IntegrityError:  # a concurrent ask for the same operation won
            return ApprovalRequest.objects.get(
                event=event, action=action, digest=digest, status=S.PENDING
            ), False
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="approval.requested",
            target=request,
            metadata={"operation": action},
        )
    return request, True


def _close(request, status, *, actor, extra=None):
    request.status = status
    request.closed_at = timezone.now()
    request.save(update_fields=["status", "closed_at"])
    record_mutation(
        actor=actor,
        workspace=request.workspace,
        action=f"approval.{status}",
        target=request,
        metadata={"operation": request.action, **(extra or {})},
    )


def _locked(request):
    return (
        ApprovalRequest.objects.select_for_update(of=("self",))
        .select_related("workspace", "event", "requested_by")
        .get(pk=request.pk)
    )


def effective_status(request, now=None):
    """What a reader should see: a request past its expiry is expired even before the sweep."""
    now = now or timezone.now()
    if request.status in (S.PENDING, S.APPROVED) and request.expires_at <= now:
        return S.EXPIRED
    return request.status


def decide(request, actor, decision, note=""):
    """Record one approver's answer; returns the updated request."""
    if decision not in ApprovalDecision.Decision.values:
        raise ValidationError({"decision": ["Use approve or reject."]})
    if len(note) > MAX_NOTE:
        raise ValidationError({"note": [f"Keep the note under {MAX_NOTE} characters."]})
    lapsed = False
    with transaction.atomic():
        request = _locked(request)
        policy = POLICIES.get(request.action)
        if policy is None or not has_any_role(actor, request.workspace, *policy.deciders):
            raise PermissionDenied("You do not have a role that permits this action.")
        if effective_status(request) == S.EXPIRED:
            lapsed = True  # recorded now, reported after this transaction commits
            if request.status != S.EXPIRED:
                _close(request, S.EXPIRED, actor=None)
        else:
            if request.status != S.PENDING:
                raise ApprovalStateError(f"The request is already {request.status}.")
            if (
                decision == ApprovalDecision.Decision.APPROVE
                and actor.pk == request.requested_by_id
                and not policy.requester_may_approve
            ):
                raise ValidationError(
                    {"detail": "The person who asked cannot approve their own request."}
                )
            try:
                with transaction.atomic():
                    ApprovalDecision.objects.create(
                        request=request, actor=actor, decision=decision, note=note
                    )
            except IntegrityError as exc:
                raise ValidationError(
                    {"detail": "You have already answered this request."}
                ) from exc
            if decision == ApprovalDecision.Decision.REJECT:
                _close(request, S.REJECTED, actor=actor, extra={"note": note})
            else:
                approved = request.decisions.filter(
                    decision=ApprovalDecision.Decision.APPROVE
                ).count()
                if approved >= request.required_approvals:
                    _close(request, S.APPROVED, actor=actor, extra={"approvals": approved})
                else:
                    record_mutation(
                        actor=actor,
                        workspace=request.workspace,
                        action="approval.decision_recorded",
                        target=request,
                        metadata={"operation": request.action, "approvals": approved},
                    )
    if lapsed:
        raise ApprovalStateError("The request has expired; ask again.")
    return request


def cancel(request, actor):
    """The requester, or a decider, withdraws a request that has not been used."""
    with transaction.atomic():
        request = _locked(request)
        policy = POLICIES.get(request.action)
        allowed = actor.pk == request.requested_by_id or (
            policy and has_any_role(actor, request.workspace, *policy.deciders)
        )
        if not allowed:
            raise PermissionDenied("You do not have a role that permits this action.")
        if request.status in TERMINAL:
            raise ApprovalStateError(f"The request is already {request.status}.")
        _close(request, S.CANCELLED, actor=actor)
    return request


def sweep(now=None):
    """Mark requests past their expiry as expired; returns how many."""
    now = now or timezone.now()
    ended = 0
    for pk in ApprovalRequest.objects.filter(
        status__in=(S.PENDING, S.APPROVED), expires_at__lte=now
    ).values_list("pk", flat=True):
        with transaction.atomic():
            request = _locked(ApprovalRequest(pk=pk))
            if request.status in (S.PENDING, S.APPROVED) and request.expires_at <= now:
                _close(request, S.EXPIRED, actor=None)
                ended += 1
    return ended


def _iso(value):
    return value.isoformat().replace("+00:00", "Z") if value else None


def describe(request, viewer=None, *, now=None):
    """The one JSON shape of a request, with what `viewer` may do with it."""
    policy = POLICIES.get(request.action)
    status = effective_status(request, now)
    decisions = list(request.decisions.select_related("actor"))
    mine = viewer is not None and any(d.actor_id == viewer.pk for d in decisions)
    is_decider = bool(
        viewer is not None and policy and has_any_role(viewer, request.workspace, *policy.deciders)
    )
    own = viewer is not None and viewer.pk == request.requested_by_id
    can_decide = (
        status == S.PENDING
        and is_decider
        and not mine
        and (not own or bool(policy and policy.requester_may_approve))
    )
    return {
        "public_id": str(request.public_id),
        "action": request.action,
        "label": policy.label if policy else request.action,
        "subject": (
            {"type": request.subject_type, "id": request.subject_id}
            if request.subject_type
            else None
        ),
        "summary": request.summary,
        "status": status,
        "requested_by": request.requested_by.username,
        "required_approvals": request.required_approvals,
        "approvals": sum(1 for d in decisions if d.decision == "approve"),
        "decisions": [
            {
                "actor": d.actor.username,
                "decision": d.decision,
                "note": d.note,
                "at": _iso(d.created_at),
            }
            for d in decisions
        ],
        "expires_at": _iso(request.expires_at),
        "created_at": _iso(request.created_at),
        "executed_at": _iso(request.executed_at),
        "can_decide": can_decide,
        "can_cancel": status in (S.PENDING, S.APPROVED) and (own or is_decider),
    }
