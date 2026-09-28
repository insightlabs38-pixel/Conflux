from .coi import conflict_pairs
from .eligibility import eligible_projects
from .models import EvaluationPoolStrategy, PoolMembership


def judge_candidates(plan, judge):
    """Projects `judge` is expected to evaluate under `plan`'s pool
    strategy, minus their own declared conflicts of interest (JUX-001).
    Shared by the rubric candidate queue and the pairwise next-pair picker
    (S01) so both judging modes draw from exactly the same eligibility rule.
    """
    candidates = eligible_projects(plan)
    if (
        plan.pool_id
        and not PoolMembership.objects.filter(pool_id=plan.pool_id, judge=judge).exists()
    ):
        return candidates.none()
    if plan.pool_strategy == EvaluationPoolStrategy.ASSIGNED_SUBSET:
        if plan.active_assignment_version_id is None:
            return candidates.none()
        candidates = candidates.filter(
            assignments__version_id=plan.active_assignment_version_id,
            assignments__judge=judge,
        )
    conflicted = {
        project_id for _, project_id in conflict_pairs(plan.stage.event_id, judge_ids={judge.id})
    }
    return candidates.exclude(id__in=conflicted)
