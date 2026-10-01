"""Internal organizer notes on projects (PD-F002-B01-T07)."""

import uuid

from core import threads
from core.authz import has_any_role
from workspaces.models import Role

from .models import Project


def _project(event, subject_id):
    try:
        key = uuid.UUID(str(subject_id))
    except ValueError:
        return None
    return Project.objects.filter(event=event, public_id=key).first()


def _organizers(user, workspace, event, subject):
    return has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN)


PROJECT = threads.register_subject(
    threads.ThreadSubject(
        key="project",
        label="Project",
        get=_project,
        describe=lambda project: f"the project {project.name}",
        audiences={"organizers": threads.AudienceRule(can_read=_organizers)},
    )
)
