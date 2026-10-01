"""Rubric versions for comparison (VERSION_DIFF, PD-F002-B02-T05): the published versions of an
evaluation plan's criteria and the live draft, for organizers and admins. Read-only; restoring
stays the rubric's own endpoint."""

import uuid

from core import version_diff
from core.authz import has_any_role
from events.models import Event
from workspaces.models import Role

from .models import EvaluationPlan

DRAFT = "draft"


def _plan(user, workspace, ref):
    if not has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN):
        return None
    try:
        event_id, plan_id = uuid.UUID(ref["event"]), uuid.UUID(ref["plan"])
    except (KeyError, ValueError):
        return None
    event = Event.objects.filter(workspace=workspace, public_id=event_id).first()
    return event and EvaluationPlan.objects.filter(stage__event=event, public_id=plan_id).first()


def versions(user, workspace, ref):
    plan = _plan(user, workspace, ref)
    if plan is None:
        return None
    published = [
        version_diff.VersionInfo(
            id=str(v.public_id),
            label=f"Version {v.number}",
            at=v.published_at.isoformat().replace("+00:00", "Z"),
        )
        for v in plan.rubric_versions.all()
    ]
    return [*published, version_diff.VersionInfo(DRAFT, "Current draft", current=True)]


def snapshot(user, workspace, ref, version_id):
    plan = _plan(user, workspace, ref)
    if plan is None:
        return False, None
    if version_id == DRAFT:
        return True, {"criteria": plan.draft_criteria}
    try:
        version = plan.rubric_versions.filter(public_id=uuid.UUID(version_id)).first()
    except ValueError:
        return False, None
    return (True, {"criteria": version.criteria}) if version else (False, None)


def register():
    version_diff.register_source(
        version_diff.VersionSource(
            "rubric", "Rubric versions", ("event", "plan"), versions, snapshot
        )
    )
