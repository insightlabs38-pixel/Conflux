from audit.services import record_mutation
from core import notifications
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from . import notifications as categories
from .approvals import require_message_approval
from .audiences import resolve_audience
from .emailing import deliver_email
from .models import Message, MessageRecipient


def send_message(*, event, actor, subject, body, audience_kind, audience_params=None):
    """Compose and deliver one message (OPS-003): resolves the audience
    *now*, persists an in-app `MessageRecipient` row for every match (the
    durable, offline-compatible baseline), then best-effort emails anyone
    with an address on file who has not turned announcement email off
    (`core.notifications`; the in-app copy is never optional). A recipient
    with no email, or a broken email transport, still gets the in-app copy --
    see `emailing.deliver_email`.
    """
    audience_params = audience_params or {}
    with transaction.atomic():
        message = create_inbox_message(
            event=event,
            actor=actor,
            subject=subject,
            body=body,
            audience_kind=audience_kind,
            audience_params=audience_params,
        )

    now = timezone.now()
    updated = []
    recipients = list(message.recipients.select_related("user").all())
    wanted = {
        user.pk
        for user in notifications.wanting(
            [r.user for r in recipients if r.user.email],
            event.workspace,
            categories.ANNOUNCEMENT,
            notifications.EMAIL,
        )
    }
    for recipient in recipients:
        if recipient.user.pk not in wanted:
            continue
        error = deliver_email(to_email=recipient.user.email, subject=subject, body=body)
        recipient.email_error = error or ""
        recipient.email_sent_at = None if error else now
        updated.append(recipient)
    if updated:
        MessageRecipient.objects.bulk_update(updated, ["email_error", "email_sent_at"])
        failures = sum(1 for item in updated if item.email_error)
        if failures:
            message.email_failure_count = failures
            message.save(update_fields=["email_failure_count"])
    return message


def create_inbox_message(*, event, actor, subject, body, audience_kind, audience_params):
    """Persist the message, recipients, and audit in the caller's transaction."""
    recipients = list(resolve_audience(event, audience_kind, audience_params))
    message = Message(
        event=event,
        sent_by=actor,
        subject=subject,
        body=body,
        audience_kind=audience_kind,
        audience_params=audience_params,
        recipient_count=len(recipients),
    )
    message.full_clean()
    message.save()
    MessageRecipient.objects.bulk_create(
        [MessageRecipient(message=message, user=user) for user in recipients]
    )
    require_message_approval(
        event=event,
        actor=actor,
        subject=subject,
        body=body,
        audience_kind=audience_kind,
        audience_params=audience_params,
        count=len(recipients),
    )
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="message.sent",
        target=message,
        metadata={"audience_kind": audience_kind, "recipient_count": len(recipients)},
        event_type="message.sent",
        payload={"event": str(event.public_id), "message": str(message.public_id)},
    )
    return message


def mark_read(recipient, actor):
    if recipient.user_id != actor.id:
        raise ValidationError("Cannot mark another user's message as read.")
    if recipient.read_at is None:
        recipient.read_at = timezone.now()
        recipient.save(update_fields=["read_at"])
    return recipient
