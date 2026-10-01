"""The first adopter of the approval primitive: a message to an audience (PD-F002-B01-T06).

Sending is irreversible and reaches many people, so an organizer can ask for a second person to
confirm it first. Off by default (setting `approvals.message_send`); the same policy gates the
single-message endpoint and the bulk planner's `send`, because both end in `create_inbox_message`.
"""

from core import approvals
from workspaces.models import Role

MESSAGE_SEND = approvals.register_policy(
    approvals.ApprovalPolicy(
        key="message_send",
        label="Sending a message to an audience",
        description=(
            "Another organizer or admin confirms the message and its audience before it is sent."
        ),
        deciders=(Role.ORGANIZER, Role.ADMIN),
    )
)


def require_message_approval(*, event, actor, subject, body, audience_kind, audience_params, count):
    """Call inside the sending transaction, after the audience is known."""
    return approvals.require_approval(
        event=event,
        actor=actor,
        action=MESSAGE_SEND.key,
        subject=("event", event.public_id),
        payload={
            "subject": subject,
            "body": body,
            "audience_kind": audience_kind,
            "audience_params": audience_params,
        },
        summary=[
            f"Send “{subject}” to {count} {'person' if count == 1 else 'people'}.",
            f"Audience: {audience_kind.replace('_', ' ')}.",
            f"Message: {body}",
        ],
    )
