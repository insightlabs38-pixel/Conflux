"""Operations center aggregate read models (OPS-001): the organizer-facing
"what's blocking this event right now" view, pulled live from the domains
that already own each fact (participation, projects, artifacts, judging,
stages, presentation, community) rather than duplicating any of it into a
new persisted table. Nothing here mutates anything.
"""

from artifacts.models import Artifact
from artifacts.preflight import run_preflight
from awards.models import Award
from community.models import AbuseSignal, VotingPlan
from django.db.models import Count, Q
from evaluations.models import EvaluationPlan
from evaluations.progress import compute_progress
from participation.models import Team, TeamMembership
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role

_LIST_LIMIT = 20


def _capped(items):
    items = list(items)
    return {"items": items[:_LIST_LIMIT], "total": len(items)}


def _participant_summary(event):
    workspace = event.workspace
    participant_count = Membership.objects.filter(
        workspace=workspace, role=Role.PARTICIPANT
    ).count()
    teamed_ids = set(
        TeamMembership.objects.filter(team__event=event).values_list("user_id", flat=True)
    )
    unteamed_ids = (
        Membership.objects.filter(workspace=workspace, role=Role.PARTICIPANT)
        .exclude(user_id__in=teamed_ids)
        .select_related("user")
        .values_list("user__username", flat=True)
    )
    blocked_teams = Team.objects.filter(event=event, projects__isnull=True).order_by("name")
    return {
        "participant_count": participant_count,
        "unteamed": _capped(unteamed_ids),
        "team_count": Team.objects.filter(event=event).count(),
        "teams_without_project": _capped(team.name for team in blocked_teams),
    }


def _submission_summary(event):
    projects = Project.objects.filter(event=event).select_related("team")
    counts = {"ready": 0, "warning": 0, "blocked": 0}
    blocked = []
    missing_artifacts = []
    for project in projects:
        if not Artifact.objects.filter(project=project).exists():
            missing_artifacts.append(project.name)
        preflight = run_preflight(project)
        counts[preflight.status.lower()] = counts.get(preflight.status.lower(), 0) + 1
        if preflight.status == "BLOCKED":
            blocked.append(
                {
                    "project": project.name,
                    "checks": [
                        check.detail for check in preflight.checks if check.severity == "blocked"
                    ],
                }
            )
    return {
        "project_count": projects.count(),
        "counts": counts,
        "blocked_projects": _capped(blocked),
        "missing_artifacts": _capped(missing_artifacts),
    }


def _judging_summary(event):
    plans = EvaluationPlan.objects.filter(stage__event=event).select_related("stage")
    rows = []
    for plan in plans:
        progress = compute_progress(plan)
        rows.append(
            {
                "plan": str(plan.public_id),
                "name": plan.name,
                "stage": plan.stage.name,
                **progress,
            }
        )
    return {"plans": rows}


def _stage_summary(event):
    stages = Stage.objects.filter(event=event).annotate(
        active_entry_count=Count("entries", filter=Q(entries__exited_at__isnull=True)),
        total_entry_count=Count("entries"),
    )
    return {
        "stages": [
            {
                "public_id": str(stage.public_id),
                "name": stage.name,
                "position": stage.position,
                "active_entries": stage.active_entry_count,
                "total_entries": stage.total_entry_count,
            }
            for stage in stages
        ]
    }


def _publication_summary(event):
    page = getattr(event, "page", None)
    awards = Award.objects.filter(event=event)
    return {
        "event_public": event.is_public,
        "page_configured": page is not None,
        "page_block_count": page.blocks.count() if page is not None else 0,
        "award_count": awards.count(),
        "awards_published": awards.filter(published_at__isnull=False).count(),
    }


def _moderation_summary(event):
    plan = VotingPlan.objects.filter(event=event).first()
    if plan is None:
        return {"voting_configured": False, "unresolved_signals": _capped([])}
    signals = AbuseSignal.objects.filter(plan=plan, resolved_at__isnull=True).order_by(
        "-occurred_at"
    )
    return {
        "voting_configured": True,
        "unresolved_signals": _capped(
            {
                "public_id": str(signal.public_id),
                "signal_type": signal.signal_type,
                "detail": signal.detail,
            }
            for signal in signals
        ),
    }


def compute_operations_summary(event) -> dict:
    return {
        "participants": _participant_summary(event),
        "submissions": _submission_summary(event),
        "judging": _judging_summary(event),
        "stages": _stage_summary(event),
        "publication": _publication_summary(event),
        "moderation": _moderation_summary(event),
    }
