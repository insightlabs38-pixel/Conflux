"""Tell people they were mentioned in a thread, through the inbox (PD-F002-B01-T07).

The notice names who mentioned them and where, never the comment text, so removing a comment
removes its content everywhere. Same precedent as the deliberation-open notice.
"""

from core import threads

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


threads.register_notifier(notify_mentions)
