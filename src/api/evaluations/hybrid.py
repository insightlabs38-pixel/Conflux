"""VS03: rubric-screening-then-pairwise hybrid evaluation.

A rubric plan screens the whole field; its close calls -- adjacent-rank
candidates whose final scores are too near each other to confidently
order -- are exactly the cases a bounded pairwise tie-break round is
worth running. This module only computes that bounded set from a rubric
plan's own already-published normalization results (never invents new
evidence); `evaluations.eligibility.eligible_projects` is what actually
enforces the bound on a linked pairwise plan (see EvaluationPlan.
hybrid_source), so a judge structurally cannot submit a comparison
outside it.
"""

from .results import ranked_results

DEFAULT_MARGIN_FRACTION = 0.05


def close_call_project_ids(
    source_plan, normalization_run, *, margin_fraction: float = DEFAULT_MARGIN_FRACTION
) -> set[int]:
    """Project ids from adjacent ranks in `normalization_run` whose final
    scores differ by at most `margin_fraction` of the run's overall score
    range -- close enough that ordinary judging noise could have swapped
    their order. Both projects in every such pair are included (a
    three-way near-tie contributes all three). A perfectly flat score
    range (every candidate tied) treats every adjacent pair as close,
    since there is no scale to measure "close" against. Never raises for
    fewer than two candidates; just returns an empty set.
    """
    results = ranked_results(source_plan, normalization_run)
    if len(results) < 2:
        return set()
    scores = [r.final_score for r in results]
    score_range = max(scores) - min(scores)
    threshold = margin_fraction * score_range
    close_ids: set[int] = set()
    for higher, lower in zip(results, results[1:]):
        gap = higher.final_score - lower.final_score
        if score_range == 0 or gap <= threshold:
            close_ids.add(higher.project_id)
            close_ids.add(lower.project_id)
    return close_ids
