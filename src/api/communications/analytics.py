from community.models import Vote, VotingPlan
from django.db.models import Count, Q
from django.utils import timezone
from evaluations.coi import conflict_pairs
from evaluations.eligibility import eligible_projects
from evaluations.models import (
    Ballot,
    EvaluationMode,
    EvaluationPlan,
    EvaluationPoolStrategy,
    PairwiseComparison,
)
from events.models import EventApplication, RegistrationStatus
from participation.models import Team, TeamMembership
from projects.models import Project, Submission, SubmissionStatus, SubmissionVersion

PLAN_PAGE_SIZE = 50


def rate(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "ratio": numerator / denominator if denominator else None,
    }


def _plan_metrics(plan):
    projects = set(eligible_projects(plan).values_list("pk", flat=True))
    judges = (
        set(plan.pool.memberships.values_list("judge_id", flat=True)) if plan.pool_id else set()
    )
    conflicts = conflict_pairs(plan.stage.event_id, judge_ids=judges, project_ids=projects)
    row = {
        "public_id": str(plan.public_id),
        "name": plan.name,
        "stage": str(plan.stage.public_id),
        "mode": plan.mode,
        "candidates": len(projects),
        "pool_judges": len(judges),
        "conflicting_pairs": len(conflicts),
    }
    if plan.mode == EvaluationMode.PAIRWISE:
        comparisons = PairwiseComparison.objects.filter(
            plan=plan, judge_id__in=judges, project_a_id__in=projects, project_b_id__in=projects
        )
        current = [
            (judge, a, b)
            for judge, a, b in comparisons.values_list("judge_id", "project_a_id", "project_b_id")
            if (judge, a) not in conflicts and (judge, b) not in conflicts
        ]
        return {
            **row,
            "completion": None,
            "current_judges": len({judge for judge, _, _ in current}),
            "pairwise_comparisons": len(current),
        }
    rubric = plan.current_rubric_version
    submitted = (
        set(
            Ballot.objects.filter(
                rubric_version=rubric,
                is_calibration=False,
                judge_id__in=judges,
                project_id__in=projects,
            ).values_list("judge_id", "project_id")
        )
        - conflicts
    )
    expected = None
    if rubric and plan.pool_id:
        if plan.pool_strategy == EvaluationPoolStrategy.ALL_JUDGES:
            expected = len(judges) * len(projects) - len(conflicts)
        elif plan.active_assignment_version_id:
            assigned = (
                set(
                    plan.active_assignment_version.assignments.filter(
                        judge_id__in=judges, project_id__in=projects
                    ).values_list("judge_id", "project_id")
                )
                - conflicts
            )
            expected = len(assigned)
            submitted &= assigned
        else:
            submitted = set()
    else:
        submitted = set()
    return {
        **row,
        "completion": rate(len(submitted), expected) if expected is not None else None,
        "current_judges": len({judge for judge, _ in submitted}),
        "pairwise_comparisons": 0,
    }


def compute_analytics(event, *, plan_offset=0):
    applications = EventApplication.objects.filter(event=event)
    memberships = TeamMembership.objects.filter(team__event=event)
    application_counts = applications.aggregate(
        approved_teamed=Count(
            "pk",
            filter=Q(status=RegistrationStatus.APPROVED, user_id__in=memberships.values("user_id")),
        ),
        **{status: Count("pk", filter=Q(status=status)) for status in RegistrationStatus.values},
    )
    approved_teamed = application_counts.pop("approved_teamed")
    application_count = sum(application_counts.values())
    teams = Team.objects.filter(event=event).aggregate(
        total=Count("pk", distinct=True),
        with_members=Count("pk", filter=Q(memberships__isnull=False), distinct=True),
        with_projects=Count("pk", filter=Q(projects__event=event), distinct=True),
    )
    projects = Project.objects.filter(event=event)
    submissions = Submission.objects.filter(project__event=event, stage__event=event)
    finalized = submissions.filter(status=SubmissionStatus.FINALIZED, current_version__isnull=False)
    project_counts = projects.aggregate(
        total=Count("pk", distinct=True),
        submitted=Count("pk", filter=Q(submissions__stage__event=event), distinct=True),
        finalized=Count(
            "pk",
            filter=Q(
                submissions__stage__event=event,
                submissions__status=SubmissionStatus.FINALIZED,
                submissions__current_version__isnull=False,
            ),
            distinct=True,
        ),
        voted=Count("pk", filter=Q(community_votes__plan__event=event), distinct=True),
    )
    plans = EvaluationPlan.objects.filter(stage__event=event).select_related(
        "stage", "pool", "active_assignment_version"
    )
    plan_count = plans.count()
    rows = [
        _plan_metrics(plan)
        for plan in plans.order_by("public_id")[plan_offset : plan_offset + PLAN_PAGE_SIZE]
    ]
    votes = Vote.objects.filter(plan__event=event, project__event=event)
    project_count = project_counts["total"]
    team_count = teams["total"]
    return {
        "event": str(event.public_id),
        "generated_at": timezone.now(),
        "registration": {
            "applications": application_count,
            "by_status": application_counts,
            "approval": rate(application_counts["approved"], application_count),
            "approved_teamed": rate(approved_teamed, application_counts["approved"]),
        },
        "teams": {
            "total": team_count,
            "with_members": teams["with_members"],
            "project_creation": rate(teams["with_projects"], team_count),
        },
        "submissions": {
            "projects": project_count,
            "with_submission": rate(project_counts["submitted"], project_count),
            "finalized_projects": rate(project_counts["finalized"], project_count),
            "draft_records": submissions.filter(status=SubmissionStatus.DRAFT).count(),
            "finalized_records": finalized.count(),
            "immutable_versions": SubmissionVersion.objects.filter(
                submission__project__event=event, submission__stage__event=event
            ).count(),
        },
        "judging": {
            "plan_count": plan_count,
            "plans": rows,
            "offset": plan_offset,
            "next_offset": plan_offset + PLAN_PAGE_SIZE
            if plan_offset + PLAN_PAGE_SIZE < plan_count
            else None,
        },
        "voting": {
            "configured": VotingPlan.objects.filter(event=event).exists(),
            "votes": votes.count(),
            "project_engagement": rate(project_counts["voted"], project_count),
        },
    }
