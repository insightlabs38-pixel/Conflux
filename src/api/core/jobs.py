"""Durable background jobs: one contract for anything too long for a request (PD-F002-B01-T05).

A feature registers a *kind* (a handler plus who may start it and the shape of its parameters) and
calls `enqueue`; it never adds a job table, a status field or a polling endpoint of its own.

Lifecycle (`TRANSITIONS`; every change happens under a row lock, so a duplicate delivery, a cancel
racing a finish and the stale sweep cannot disagree):

    queued -> running -> succeeded | failed | cancelling -> cancelled
    queued -> cancelled

Rules
- `enqueue` is authorised against the kind's roles, validates `params` with the kind's serializer,
  refuses secret-looking keys and oversized input, dedupes by (requester, kind, idempotency key)
  and audits the request. The worker is started only after the transaction commits.
- `run` is safe to deliver twice: only a `queued` job starts. The requester's role is checked again
  at run time. A handler gets a `JobContext` (progress, log, cooperative cancel, artifacts); what
  it raises becomes the failure shown to the user (`ValidationError` text is shown, anything else
  is a generic "unexpected" with the detail only in the server log).
- Cancellation is cooperative: a queued job is cancelled at once, a running one becomes
  `cancelling` and ends when the handler next calls `ctx.checkpoint()`. Work already done by a
  handler is never rolled back by the platform; a handler that must be all-or-nothing wraps its own
  writes in one transaction. A handler that finishes anyway despite a cancel request is
  `succeeded`, because that is what happened.
- `result` (<= 64 KB) and `params` (<= 16 KB) are bounded JSON, secrets never belong in params,
  results or logs, anything larger is an artifact (<= 25 MB each). Logs keep the newest 500 lines.
- `sweep` fails a running job that stopped reporting (its kind's `timeout`) and re-sends jobs that
  were queued but never started (a lost message, a broker outage at enqueue time).
"""

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.utils.encoders import JSONEncoder

from .authz import has_any_role
from .models import Job, JobArtifact, JobLog

log = logging.getLogger(__name__)

MAX_PARAMS_BYTES = 16 * 1024
MAX_RESULT_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 25 * 1024 * 1024
MAX_LOG_LINES = 500
MAX_ACTIVE_PER_USER = 10
REDISPATCH_AFTER = timedelta(seconds=60)
DEFAULT_TIMEOUT = 300  # seconds without a heartbeat before a running job is failed
_SECRET_KEYS = ("password", "secret", "token", "api_key", "apikey", "authorization", "credential")
_ARTIFACT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")

S = Job.Status
TRANSITIONS = {
    S.QUEUED: {S.RUNNING, S.CANCELLED, S.FAILED},
    S.RUNNING: {S.SUCCEEDED, S.FAILED, S.CANCELLING},
    S.CANCELLING: {S.CANCELLED, S.SUCCEEDED, S.FAILED},
    S.SUCCEEDED: set(),
    S.FAILED: set(),
    S.CANCELLED: set(),
}
TERMINAL = frozenset(status for status, targets in TRANSITIONS.items() if not targets)


class JobCancelled(Exception):
    """Raised by `JobContext.checkpoint()` when cancellation was requested."""


class _Unsafe(Exception):
    """A handler's result broke the platform's limits (internal)."""


class JobStateError(Exception):
    """The job is not in a state that allows this (e.g. cancelling a finished job)."""


@dataclass(frozen=True)
class JobKind:
    """One kind of background work. `handler(ctx)` returns a JSON-able result dict (or None).

    `params` is a serializer class validating the input; `roles` who may start it (and the only
    ones who may see its jobs besides the requester); `event_scoped` kinds need an event.
    """

    key: str
    label: str
    handler: Callable
    roles: tuple = ()
    params: type | None = None
    event_scoped: bool = True
    timeout: int = DEFAULT_TIMEOUT


KINDS: dict[str, JobKind] = {}


def register_kind(kind: JobKind):
    """Add a kind once; a different registration under a taken key is a bug."""
    if kind.key in KINDS and KINDS[kind.key] != kind:
        raise ValueError(f"Job kind {kind.key!r} is already registered")
    KINDS[kind.key] = kind
    return kind


def _size(value):
    return len(json.dumps(value, cls=JSONEncoder, separators=(",", ":")).encode())


def _find_secret(value, path=""):
    """The path of the first secret-looking key in a nested value, else None."""
    if isinstance(value, dict):
        for key, item in value.items():
            if any(word in str(key).lower() for word in _SECRET_KEYS):
                return f"{path}{key}"
            found = _find_secret(item, f"{path}{key}.")
            if found:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = _find_secret(item, f"{path}{index}.")
            if found:
                return found
    return None


def _validated_params(kind, raw):
    secret = _find_secret(raw)  # before validation: a serializer would silently drop the key
    if secret:
        raise ValidationError({"params": [f"{secret}: secrets cannot be passed to a job."]})
    if kind.params is None:
        if raw:
            raise ValidationError({"params": ["This kind of job takes no parameters."]})
        return {}
    checked = kind.params(data=raw if raw is not None else {})
    checked.is_valid(raise_exception=True)
    params = json.loads(json.dumps(dict(checked.validated_data), cls=JSONEncoder))
    if _size(params) > MAX_PARAMS_BYTES:
        raise ValidationError({"params": ["Job parameters are too large."]})
    return params


def dispatch(public_id):
    """Hand a queued job to a worker. Never raises: the sweep re-sends what did not arrive."""
    try:
        from .tasks import run_job

        run_job.delay(str(public_id))
    except Exception:  # noqa: BLE001 - a broker outage must not fail the request that enqueued
        log.warning("job %s could not be sent to a worker; the sweep will retry", public_id)


def enqueue(*, kind, actor, workspace, event=None, params=None, idempotency_key=""):
    """Create a queued job and return `(job, created)`; call from a request or another job."""
    spec = KINDS.get(kind)
    if spec is None:
        raise ValidationError({"kind": ["Unknown kind of job."]})
    if not has_any_role(actor, workspace, *spec.roles):
        raise PermissionDenied("You do not have a role that permits this action.")
    if spec.event_scoped and event is None:
        raise ValidationError({"event": ["This kind of job belongs to an event."]})
    if event is not None and event.workspace_id != workspace.pk:
        raise ValidationError({"event": ["The event is not in this workspace."]})
    if len(idempotency_key) > 100:
        raise ValidationError({"idempotency_key": ["The key is too long."]})
    clean = _validated_params(spec, params)
    with transaction.atomic():
        if idempotency_key:
            existing = Job.objects.filter(
                requested_by=actor, kind=kind, idempotency_key=idempotency_key
            ).first()
            if existing:
                if existing.params != clean:
                    raise ValidationError(
                        {"idempotency_key": ["This key was already used with different input."]}
                    )
                return existing, False
        active = Job.objects.filter(
            requested_by=actor, status__in=(S.QUEUED, S.RUNNING, S.CANCELLING)
        ).count()
        if active >= MAX_ACTIVE_PER_USER:
            raise ValidationError({"detail": "Too many jobs are already running; wait for one."})
        try:
            with transaction.atomic():
                job = Job.objects.create(
                    workspace=workspace,
                    event=event,
                    kind=kind,
                    params=clean,
                    requested_by=actor,
                    idempotency_key=idempotency_key,
                )
        except IntegrityError:  # a concurrent request with the same key won
            return Job.objects.get(
                requested_by=actor, kind=kind, idempotency_key=idempotency_key
            ), False
        record_mutation(
            actor=actor,
            workspace=workspace,
            action="job.requested",
            target=job,
            metadata={"kind": kind, "event": str(event.public_id) if event else None},
        )
        transaction.on_commit(lambda: dispatch(job.public_id))
    return job, True


class JobContext:
    """What a handler sees. Each call commits on its own, so progress is visible while it runs."""

    def __init__(self, job):
        self._pk = job.pk
        self.public_id = job.public_id
        self.params = job.params
        self.workspace = job.workspace
        self.event = job.event
        self.actor = job.requested_by

    def heartbeat(self):
        Job.objects.filter(pk=self._pk).update(heartbeat_at=timezone.now())

    def progress(self, done=None, total=None, message=""):
        for name, value in (("done", done), ("total", total)):
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(f"progress {name} must be a non-negative integer")
        Job.objects.filter(pk=self._pk).update(
            progress_done=done,
            progress_total=total,
            progress_message=str(message)[:200],
            heartbeat_at=timezone.now(),
        )

    def log(self, message, level="info"):
        JobLog.objects.create(job_id=self._pk, level=str(level)[:8], message=str(message)[:500])
        extra = JobLog.objects.filter(job_id=self._pk).count() - MAX_LOG_LINES
        if extra > 0:
            oldest = JobLog.objects.filter(job_id=self._pk).values_list("pk", flat=True)[:extra]
            JobLog.objects.filter(pk__in=list(oldest)).delete()
        self.heartbeat()

    @property
    def cancelled(self):
        self.heartbeat()
        return Job.objects.filter(pk=self._pk, status=S.CANCELLING).exists()

    def checkpoint(self):
        """Call between units of work: stops the handler when the user asked to cancel."""
        if self.cancelled:
            raise JobCancelled()

    def artifact(self, name, content_type, data):
        if not _ARTIFACT_NAME.match(name):
            raise ValueError("artifact names are letters, digits, dot, dash and underscore")
        body = data.encode() if isinstance(data, str) else bytes(data)
        if len(body) > MAX_ARTIFACT_BYTES:
            raise ValidationError({"artifact": ["The output is too large to keep."]})
        JobArtifact.objects.update_or_create(
            job_id=self._pk,
            name=name,
            defaults={"content_type": content_type, "size": len(body), "body": body},
        )
        self.heartbeat()


def _finish(pk, target, *, result=None, error=None):
    """Move a job to a terminal state if the graph allows it; returns the job."""
    with transaction.atomic():
        job = Job.objects.select_for_update(of=("self",)).select_related("workspace").get(pk=pk)
        if target not in TRANSITIONS[job.status]:
            return job
        job.status = target
        job.result = result
        job.error = error
        job.finished_at = timezone.now()
        if target == S.SUCCEEDED and job.progress_total is not None:
            job.progress_done = job.progress_total  # a finished job reads as complete
        job.save(update_fields=["status", "result", "error", "finished_at", "progress_done"])
        record_mutation(
            actor=job.requested_by,
            workspace=job.workspace,
            action=f"job.{target}",
            target=job,
            metadata={"kind": job.kind, **({"error": error["code"]} if error else {})},
        )
    return job


def run(public_id):
    """Execute one queued job (called by the worker); a second delivery does nothing."""
    with transaction.atomic():
        job = (
            Job.objects.select_for_update(of=("self",))
            .select_related("workspace", "event", "requested_by")
            .filter(public_id=public_id)
            .first()
        )
        if job is None or job.status != S.QUEUED:
            return job
        job.status = S.RUNNING
        job.attempts += 1
        job.started_at = job.heartbeat_at = timezone.now()
        job.save(update_fields=["status", "attempts", "started_at", "heartbeat_at"])
    kind = KINDS.get(job.kind)
    if kind is None:
        return _finish(
            job.pk, S.FAILED, error={"code": "unknown_kind", "message": "This job cannot run."}
        )
    if not has_any_role(job.requested_by, job.workspace, *kind.roles):
        return _finish(
            job.pk,
            S.FAILED,
            error={"code": "forbidden", "message": "The requester no longer has access."},
        )
    ctx = JobContext(job)
    try:
        result = kind.handler(ctx)
        result = {} if result is None else result
        if _find_secret(result):
            raise _Unsafe("The job's result contained a secret.")
        if _size(result) > MAX_RESULT_BYTES:
            raise _Unsafe("The job's result is too large; attach it as an artifact.")
        return _finish(job.pk, S.SUCCEEDED, result=json.loads(json.dumps(result, cls=JSONEncoder)))
    except JobCancelled:
        return _finish(job.pk, S.CANCELLED)
    except _Unsafe as exc:
        log.error("job %s: %s", public_id, exc)
        return _finish(job.pk, S.FAILED, error={"code": "unsafe_result", "message": str(exc)})
    except (ValidationError, ModelValidationError) as exc:
        return _finish(job.pk, S.FAILED, error={"code": "invalid", "message": _message(exc)})
    except Exception:  # noqa: BLE001 - the detail stays in the server log, never in the response
        log.exception("job %s (%s) failed", public_id, job.kind)
        return _finish(
            job.pk,
            S.FAILED,
            error={"code": "internal", "message": "The job failed unexpectedly. Try again."},
        )


def _message(exc):
    detail = getattr(exc, "detail", None)
    if detail is None:
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
    text = json.dumps(detail, cls=JSONEncoder) if not isinstance(detail, str) else detail
    return text[:500]


def cancel(job, actor):
    """Ask a job to stop. Returns the job; a finished job raises `JobStateError`."""
    with transaction.atomic():
        job = Job.objects.select_for_update(of=("self",)).select_related("workspace").get(pk=job.pk)
        if job.status in TERMINAL:
            raise JobStateError("The job has already finished.")
        if job.status == S.CANCELLING:
            return job
        job.status = S.CANCELLED if job.status == S.QUEUED else S.CANCELLING
        if job.status == S.CANCELLED:
            job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at"])
        record_mutation(
            actor=actor,
            workspace=job.workspace,
            action="job.cancelled" if job.status == S.CANCELLED else "job.cancel_requested",
            target=job,
            metadata={"kind": job.kind},
        )
    return job


def sweep(now=None):
    """Fail running jobs that stopped reporting and re-send queued ones that never started."""
    now = now or timezone.now()
    failed = redispatched = 0
    for job in Job.objects.filter(status__in=(S.RUNNING, S.CANCELLING)).select_related("workspace"):
        kind = KINDS.get(job.kind)
        limit = timedelta(seconds=kind.timeout if kind else DEFAULT_TIMEOUT)
        if (job.heartbeat_at or job.started_at or job.created_at) >= now - limit:
            continue
        if job.status == S.CANCELLING:
            _finish(job.pk, S.CANCELLED)
        else:
            _finish(
                job.pk,
                S.FAILED,
                error={
                    "code": "timeout",
                    "message": "The job stopped reporting progress and was ended. Try again.",
                },
            )
        failed += 1
    for public_id in Job.objects.filter(
        status=S.QUEUED, created_at__lt=now - REDISPATCH_AFTER
    ).values_list("public_id", flat=True):
        dispatch(public_id)
        redispatched += 1
    return {"ended": failed, "redispatched": redispatched}


def describe(job, *, detail=False):
    """The one JSON shape of a job; `detail` adds the log trail."""
    progress = None
    if job.progress_done is not None or job.progress_message:
        progress = {
            "done": job.progress_done,
            "total": job.progress_total,
            "message": job.progress_message,
        }
    kind = KINDS.get(job.kind)
    body = {
        "public_id": str(job.public_id),
        "kind": job.kind,
        "label": kind.label if kind else job.kind,
        "status": job.status,
        "event": str(job.event.public_id) if job.event_id else None,
        "requested_by": job.requested_by.username,
        "progress": progress,
        "result": job.result,
        "error": job.error,
        "cancellable": job.status in (S.QUEUED, S.RUNNING),
        "created_at": job.created_at.isoformat().replace("+00:00", "Z"),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "artifacts": [
            {"name": a.name, "content_type": a.content_type, "size": a.size}
            for a in job.artifacts.defer("body")
        ],
    }
    if detail:
        body["params"] = job.params
        body["logs"] = [
            {"level": line.level, "message": line.message, "at": _iso(line.created_at)}
            for line in job.logs.all()
        ]
    return body


def _iso(value):
    return value.isoformat().replace("+00:00", "Z") if value else None
