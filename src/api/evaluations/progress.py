"""Organizer progress/judging-health summary (JUX-004): coverage, load,
completion and normalization state in one place, so an organizer can see
whether judging is actually on track without cross-referencing four
different endpoints by hand.
"""

from django.db.models import Count

from .coi import conflict_pairs
from .eligibility import eligible_projects
from .models import Ballot, EvaluationPoolStrategy


def compute_progress(plan) -> dict:
    candidates = eligible_projects(plan)
    candidate_count = candidates.count()

    pool_judge_ids = (
        set(plan.pool.memberships.values_list("judge_id", flat=True)) if plan.pool_id else set()
    )
    pool_judge_count = len(pool_judge_ids)
    conflict_count = len(
        conflict_pairs(
            plan.stage.event_id,
            judge_ids=pool_judge_ids,
            project_ids=set(candidates.values_list("id", flat=True)),
        )
    )

    if (
        plan.pool_strategy == EvaluationPoolStrategy.ASSIGNED_SUBSET
        and plan.active_assignment_version_id
    ):
        expected_ballots = plan.active_assignment_version.assignments.count()
    elif plan.pool_strategy == EvaluationPoolStrategy.ALL_JUDGES and pool_judge_count:
        expected_ballots = max(pool_judge_count * candidate_count - conflict_count, 0)
    else:
        expected_ballots = None

    # Calibration ballots (S02) are practice evidence, never live judging
    # evidence -- excluded here the same way scoring.ballot_observations
    # excludes them from normalization.
    submitted = Ballot.objects.filter(rubric_version__plan=plan, is_calibration=False).count()
    ratio = (submitted / expected_ballots) if expected_ballots else None

    latest_run = plan.normalization_runs.order_by("-number").first()

    calibration_project_count = plan.calibration_projects.count()
    calibration_overview = None
    if calibration_project_count:
        judges_complete = (
            Ballot.objects.filter(rubric_version__plan=plan, is_calibration=True)
            .values("judge_id")
            .annotate(completed=Count("project_id", distinct=True))
            .filter(completed__gte=calibration_project_count)
            .count()
        )
        calibration_overview = {
            "required": plan.calibration_required,
            "project_count": calibration_project_count,
            "judges_total": pool_judge_count,
            "judges_complete": judges_complete,
        }

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
        "calibration": calibration_overview,
    }
