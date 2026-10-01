"""Tell people they were mentioned in a thread, through the inbox (PD-F002-B01-T07).

The notice names who mentioned them and where, never the comment text, so removing a comment
removes its content everywhere. Same precedent as the deliberation-open notice.
"""

from core import notifications, threads

from . import notifications as categories
from .emailing import deliver_email
from .models import Message, MessageRecipient

KIND = "thread_mention"


def notify_mentions(event, actor, users, label):
    message = Message.objects.create(
        event=event,
        sent_by=actor,
        subject=f"@{actor.username} mentioned you",
        body=f"In {label}. Open it in the event dashboard to read the comment.",
        audience_kind=KIND,
        recipient_count=len(users),
    )
    MessageRecipient.objects.bulk_create([MessageRecipient(message=message, user=u) for u in users])
    # The inbox notice is always kept; email is for people who asked for mention emails (off by
    # default, so nothing changes for anyone who has not chosen). Never the comment text.
    for user in notifications.wanting(
        [u for u in users if u.email], event.workspace, categories.MENTION, notifications.EMAIL
    ):
        deliver_email(to_email=user.email, subject=message.subject, body=message.body)


threads.register_notifier(notify_mentions)
