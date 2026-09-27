from django.core.exceptions import ValidationError
from django.db import transaction
from participation.models import TeamMembership

from .models import Project, ProjectMembership, ProjectMembershipRole


@transaction.atomic
def create_project(event, creator, name, *, team=None, description=""):
    if not event.workspace.memberships.filter(user=creator).exists():
        raise ValidationError("Creator must belong to the event workspace.")
    if team and not TeamMembership.objects.filter(team=team, user=creator).exists():
        raise ValidationError("Creator must belong to the project team.")
    project = Project(
        event=event, team=team, name=name, description=description, created_by=creator
    )
    project.full_clean()
    project.save()
    membership = ProjectMembership(project=project, user=creator, role=ProjectMembershipRole.OWNER)
    membership.full_clean()
    membership.save()
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
