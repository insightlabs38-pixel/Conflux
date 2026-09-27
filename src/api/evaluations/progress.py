"""Organizer progress/judging-health summary (JUX-004): coverage, load,
completion and normalization state in one place, so an organizer can see
whether judging is actually on track without cross-referencing four
different endpoints by hand.
"""

from projects.models import Project

from .models import Ballot, ConflictOfInterest, EvaluationPoolStrategy


def compute_progress(plan) -> dict:
    candidates = Project.objects.filter(
        event_id=plan.stage.event_id, submissions__stage=plan.stage
    ).distinct()
    candidate_count = candidates.count()

    pool_judge_count = plan.pool.memberships.count() if plan.pool_id else 0
    conflict_count = ConflictOfInterest.objects.filter(event_id=plan.stage.event_id).count()

    if (
        plan.pool_strategy == EvaluationPoolStrategy.ASSIGNED_SUBSET
        and plan.active_assignment_version_id
    ):
        expected_ballots = plan.active_assignment_version.assignments.count()
    elif plan.pool_strategy == EvaluationPoolStrategy.ALL_JUDGES and pool_judge_count:
        expected_ballots = max(pool_judge_count * candidate_count - conflict_count, 0)
    else:
        expected_ballots = None

    submitted = Ballot.objects.filter(rubric_version__plan=plan).count()
    ratio = (submitted / expected_ballots) if expected_ballots else None

    latest_run = plan.normalization_runs.order_by("-number").first()

    return {
        "candidate_count": candidate_count,
        "pool_judge_count": pool_judge_count,
        "conflict_count": conflict_count,
        "expected_ballots": expected_ballots,
        "submitted_ballots": submitted,
        "completion_ratio": ratio,
        "rubric_published": plan.current_rubric_version is not None,
        "assignment_active": plan.active_assignment_version_id is not None,
        "latest_normalization_run": (
            {
                "number": latest_run.number,
                "converged": latest_run.converged,
                "low_information_judges": len(
                    latest_run.evidence.get("low_information_judges", [])
                ),
            }
            if latest_run
            else None
        ),
        "results_published": plan.published_normalization_run_id is not None,
    }
