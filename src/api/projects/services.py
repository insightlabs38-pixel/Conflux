from audit.services import record_mutation
from django.core.exceptions import ValidationError
from django.db import transaction
from participation.models import TeamMembership

from .models import Project, ProjectMembership, ProjectMembershipRole


@transaction.atomic
def create_project(event, creator, name, *, team=None, track=None, description=""):
    if not event.workspace.memberships.filter(user=creator).exists():
        raise ValidationError("Creator must belong to the event workspace.")
    if team and not TeamMembership.objects.filter(team=team, user=creator).exists():
        raise ValidationError("Creator must belong to the project team.")
    project = Project(
        event=event,
        team=team,
        track=track,
        name=name,
        description=description,
        created_by=creator,
    )
    project.full_clean()
    project.save()
    membership = ProjectMembership(project=project, user=creator, role=ProjectMembershipRole.OWNER)
    membership.full_clean()
    membership.save()
    record_mutation(
        actor=creator,
        workspace=event.workspace,
        action="project.created",
        target=project,
        metadata={"event_id": str(event.public_id)},
    )
    return project


@transaction.atomic
def update_project(project, actor, *, name=None, description=None, track=None, track_set=False):
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only a project member can edit this project.")
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if track_set:
        project.track = track
    stored = Project.objects.get(pk=project.pk)
    changed = [
        field
        for field in ("name", "description", "track_id")
        if getattr(stored, field) != getattr(project, field)
    ]
    project.full_clean()
    project.save()
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="project.updated",
        target=project,
        metadata={
            "event_id": str(project.event.public_id),
            "changed_fields": [f.removesuffix("_id") for f in changed],
        },
    )
    return project


@transaction.atomic
def add_project_member(project, actor, user):
    if not project.memberships.filter(user=actor, role=ProjectMembershipRole.OWNER).exists():
        raise ValidationError("Only a project owner can add members.")
    membership = ProjectMembership(
        project=project, user=user, role=ProjectMembershipRole.CONTRIBUTOR
    )
    membership.full_clean()
    membership.save()
    return membership
