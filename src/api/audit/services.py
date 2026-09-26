from django.db import transaction

from .models import AuditEvent, DomainEvent


def record_mutation(
    *, actor, workspace, action, target=None, metadata=None, event_type=None, payload=None
):
    """Write an AuditEvent (evidence) and, if `event_type` is given, a pending
    DomainEvent (async intent) atomically with the caller's mutation.

    Must be called from inside the same transaction as the mutation it
    documents: that's the whole point of the outbox pattern, so a rolled-back
    mutation can never leave behind audit/event rows describing something
    that didn't happen.
    """
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("record_mutation must run inside an atomic transaction")

    audit_event = AuditEvent.objects.create(
        workspace=workspace,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=target.__class__.__name__ if target is not None else "",
        target_id=str(getattr(target, "public_id", "")) if target is not None else "",
        metadata=metadata or {},
    )

    domain_event = None
    if event_type:
        domain_event = DomainEvent.objects.create(
            workspace=workspace, event_type=event_type, payload=payload or {}
        )

    return audit_event, domain_event
