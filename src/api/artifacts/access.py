"""Who may see which submitted artifact (PVS08), shared by reviewer views and previews.

Judges see only what an artifact's visibility grants their role, and only for projects they are
expected to evaluate; organizers see everything in their workspace; project members see their own.
"""

from core.authz import has_any_role
from evaluations.candidates import judge_candidates
from evaluations.models import EvaluationPlan
from workspaces.models import Role

from .models import ArtifactVisibility


def reviewer_scope(user, workspace, project):
    """'all', 'member', 'judge' or None for `user` on this project."""
    if has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN):
        return "all"
    if project.memberships.filter(user=user).exists():
        return "member"
    if has_any_role(user, workspace, Role.JUDGE):
        plans = EvaluationPlan.objects.filter(stage__event=project.event)
        if any(judge_candidates(plan, user).filter(pk=project.pk).exists() for plan in plans):
            return "judge"
    return None


def visible(artifact, scope):
    if scope in ("all", "member"):
        return True
    return artifact.visibility in (ArtifactVisibility.PUBLIC, ArtifactVisibility.JUDGE)
