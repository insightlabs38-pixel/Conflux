"""Form versions for comparison (VERSION_DIFF, PD-F002-B02-T05): the published versions and the
live draft, for organizers and admins of the form's workspace. Read-only; restoring stays the
form's own endpoint."""

import uuid

from core import version_diff
from core.authz import has_any_role
from events.models import Event
from workspaces.models import Role

from .models import FormDefinition

DRAFT = "draft"


def _form(user, workspace, ref):
    if not has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN):
        return None
    try:
        event_id, form_id = uuid.UUID(ref["event"]), uuid.UUID(ref["form"])
    except (KeyError, ValueError):
        return None
    event = Event.objects.filter(workspace=workspace, public_id=event_id).first()
    return event and FormDefinition.objects.filter(event=event, public_id=form_id).first()


def versions(user, workspace, ref):
    form = _form(user, workspace, ref)
    if form is None:
        return None
    published = [
        version_diff.VersionInfo(
            id=str(v.public_id),
            label=f"Version {v.number}",
            at=v.published_at.isoformat().replace("+00:00", "Z"),
        )
        for v in form.versions.all()
    ]
    return [*published, version_diff.VersionInfo(DRAFT, "Current draft", current=True)]


def snapshot(user, workspace, ref, version_id):
    form = _form(user, workspace, ref)
    if form is None:
        return False, None
    if version_id == DRAFT:
        return True, form.draft_schema
    try:
        version = form.versions.filter(public_id=uuid.UUID(version_id)).first()
    except ValueError:
        return False, None
    return (True, version.schema) if version else (False, None)


def register():
    version_diff.register_source(
        version_diff.VersionSource("form", "Form versions", ("event", "form"), versions, snapshot)
    )
