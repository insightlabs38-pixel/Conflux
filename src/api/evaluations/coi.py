"""Central hard-conflict calculation shared by judging and assignment."""

from collections import defaultdict

from participation.models import TeamMembership
from projects.models import Project, ProjectMembership

from .models import (
    COIRelationshipKind,
    COIRule,
    COIRuleKind,
    ConflictOfInterest,
    JudgeCOIRelationship,
    ProjectCOIAttribute,
)


def conflict_pairs(event_id, *, judge_ids=None, project_ids=None) -> set[tuple[int, int]]:
    """Return direct recusals plus enabled exact relationship matches."""
    direct = ConflictOfInterest.objects.filter(event_id=event_id)
    projects = Project.objects.filter(event_id=event_id)
    relationships = JudgeCOIRelationship.objects.filter(event_id=event_id)
    memberships = TeamMembership.objects.filter(team__event_id=event_id)
    if judge_ids is not None:
        direct = direct.filter(judge_id__in=judge_ids)
        relationships = relationships.filter(judge_id__in=judge_ids)
        memberships = memberships.filter(user_id__in=judge_ids)
    if project_ids is not None:
        direct = direct.filter(project_id__in=project_ids)
        projects = projects.filter(id__in=project_ids)

    pairs = set(direct.values_list("judge_id", "project_id"))
    enabled = {kind: True for kind in COIRuleKind.values}
    enabled.update(COIRule.objects.filter(event_id=event_id).values_list("kind", "enabled"))
    project_rows = list(projects.values_list("id", "team_id", "created_by_id"))
    project_ids_in_scope = [project_id for project_id, _, _ in project_rows]
    if enabled[COIRuleKind.PROJECT_CREATOR]:
        pairs.update(
            (creator_id, project_id)
            for project_id, _, creator_id in project_rows
            if judge_ids is None or creator_id in judge_ids
        )
    if enabled[COIRuleKind.PROJECT_MEMBERSHIP]:
        project_members = ProjectMembership.objects.filter(project_id__in=project_ids_in_scope)
        if judge_ids is not None:
            project_members = project_members.filter(user_id__in=judge_ids)
        pairs.update(project_members.values_list("user_id", "project_id"))

    by_team = defaultdict(set)
    for project_id, team_id, _ in project_rows:
        if team_id is not None:
            by_team[team_id].add(project_id)
    team_judges = defaultdict(set)
    if enabled[COIRuleKind.TEAM_MEMBERSHIP]:
        for team_id, user_id in memberships.values_list("team_id", "user_id"):
            team_judges[team_id].add(user_id)
    for team_id, judge_id in relationships.filter(kind=COIRelationshipKind.TEAM).values_list(
        "team_id", "judge_id"
    ):
        team_judges[team_id].add(judge_id)
    for team_id, project_set in by_team.items():
        pairs.update(
            (judge_id, project_id)
            for judge_id in team_judges[team_id]
            for project_id in project_set
        )

    projects_by_value = defaultdict(set)
    for project_id, kind, value in ProjectCOIAttribute.objects.filter(
        project_id__in=project_ids_in_scope
    ).values_list("project_id", "kind", "value"):
        projects_by_value[(kind, value)].add(project_id)
    for kind, value, judge_id in relationships.exclude(kind=COIRelationshipKind.TEAM).values_list(
        "kind", "value", "judge_id"
    ):
        pairs.update((judge_id, project_id) for project_id in projects_by_value[(kind, value)])
    return pairs


def is_conflicted(event_id, judge_id, project_id) -> bool:
    return (judge_id, project_id) in conflict_pairs(
        event_id, judge_ids={judge_id}, project_ids={project_id}
    )
