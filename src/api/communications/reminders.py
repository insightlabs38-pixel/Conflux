from datetime import timedelta

from core.authz import has_any_role
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from workspaces.models import Role

from .models import Reminder
from .services import create_inbox_message


def dispatch_due_reminders(*, at=None, limit=100):
    now = at or timezone.now()
    ids = list(
        Reminder.objects.filter(
            due_at__lte=now, sent_message__isnull=True, cancelled_at__isnull=True
        )
        .filter(Q(retry_after__isnull=True) | Q(retry_after__lte=now))
        .order_by("due_at", "id")
        .values_list("id", flat=True)[:limit]
    )
    sent = 0
    for reminder_id in ids:
        with transaction.atomic():
            reminder = (
                Reminder.objects.select_for_update(of=("self",))
                .select_related("event__workspace", "created_by")
                .get(pk=reminder_id)
            )
            if (
                reminder.sent_message_id
                or reminder.cancelled_at
                or reminder.due_at > now
                or (reminder.retry_after and reminder.retry_after > now)
            ):
                continue
            try:
                if not has_any_role(
                    reminder.created_by, reminder.event.workspace, Role.ORGANIZER, Role.ADMIN
                ):
                    raise ValidationError("The reminder's organizer no longer has permission.")
                with transaction.atomic():
                    message = create_inbox_message(
                        event=reminder.event,
                        actor=reminder.created_by,
                        subject=reminder.subject,
                        body=reminder.body,
                        audience_kind=reminder.audience_kind,
                        audience_params=reminder.audience_params,
                    )
            except ValidationError as exc:
                reminder.last_error = "; ".join(exc.messages)[:300]
                reminder.retry_after = now + timedelta(minutes=10)
                reminder.save(update_fields=["last_error", "retry_after"])
                continue
            reminder.sent_message = message
            reminder.last_error = ""
            reminder.retry_after = None
            reminder.save(update_fields=["sent_message", "last_error", "retry_after"])
            sent += 1
    return sent
