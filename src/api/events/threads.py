"""Internal organizer notes on registration applications (PD-F002-B01-T07)."""

import uuid

from core import threads
from core.authz import has_any_role
from workspaces.models import Role

from .models import EventApplication


def _application(event, subject_id):
    try:
        key = uuid.UUID(str(subject_id))
    except ValueError:
        return None
    return (
        EventApplication.objects.filter(event=event, public_id=key).select_related("user").first()
    )


def _organizers(user, workspace, event, subject):
    return has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN)


APPLICATION = threads.register_subject(
    threads.ThreadSubject(
        key="application",
        label="Application",
        get=_application,
        describe=lambda application: f"the application of @{application.user.username}",
        audiences={"organizers": threads.AudienceRule(can_read=_organizers)},
    )
)
