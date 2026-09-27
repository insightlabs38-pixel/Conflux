"""Ranked results with deterministic tie-breaking (JUX-005, S01).

A project's rank is driven by its published run's headline score (a
NormalizationRun's final score, or a PairwiseRun's Bradley-Terry
strength). Exactly-equal scores are broken by the plan's `tie_breaks` (an
organizer-assigned integer per project, lower wins), and anything still
tied after that falls back to project public_id -- so the ordering is
always fully deterministic, never dependent on dict/query iteration order.
The same `tie_breaks` field is shared by both evaluation modes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RankedResult:
    rank: int
    project_id: int
    raw_score: float | None
    final_score: float
    tie_break: int | None


@dataclass(frozen=True)
class PairwiseRankedResult:
    rank: int
    project_id: int
    strength: float
    win_count: float
    comparison_count: float
    tie_break: int | None


def _tie_broken_order(project_ids, score_for, tie_breaks) -> list:
    return sorted(project_ids, key=lambda p: (-score_for(p), tie_breaks.get(str(p), 0), p))


def ranked_results(plan, normalization_run) -> list[RankedResult]:
    if normalization_run.plan_id != plan.id:
        raise ValueError("normalization_run does not belong to this plan.")

    tie_breaks = plan.tie_breaks or {}

    # NormalizationRun.evidence stores each project's raw/final score
    # directly (see normalization.run): that's the frozen evidence for this
    # exact run, not whatever the live ballots say now (more may have been
    # cast since), so results stay reproducible for a given published run.
    projects_evidence = normalization_run.evidence.get("projects", {})

    def final_score_for(project_id):
        entry = projects_evidence.get(str(project_id))
        if entry is not None:
            return entry["final"]
        return normalization_run.grand_mean

    def raw_score_for(project_id):
        entry = projects_evidence.get(str(project_id))
        return entry["raw"] if entry is not None else None

    all_project_ids = sorted(int(k) for k in projects_evidence)
    ordered = _tie_broken_order(all_project_ids, final_score_for, tie_breaks)
    return [
        RankedResult(
            rank=index + 1,
            project_id=project_id,
            raw_score=raw_score_for(project_id),
            final_score=final_score_for(project_id),
            tie_break=tie_breaks.get(str(project_id)),
        )
        for index, project_id in enumerate(ordered)
    ]


def pairwise_ranked_results(plan, pairwise_run) -> list[PairwiseRankedResult]:
    if pairwise_run.plan_id != plan.id:
        raise ValueError("pairwise_run does not belong to this plan.")

    tie_breaks = plan.tie_breaks or {}

    # PairwiseRun.evidence stores each project's strength/win/comparison
    # counts directly (see pairwise.run): frozen evidence for this exact
    # run, not whatever comparisons exist now -- same reproducibility
    # guarantee as ranked_results above.
    projects_evidence = pairwise_run.evidence.get("projects", {})

    def strength_for(project_id):
        entry = projects_evidence.get(str(project_id))
        return entry["strength"] if entry is not None else 1.0

    all_project_ids = sorted(int(k) for k in projects_evidence)
    ordered = _tie_broken_order(all_project_ids, strength_for, tie_breaks)
    return [
        PairwiseRankedResult(
            rank=index + 1,
            project_id=project_id,
            strength=strength_for(project_id),
            win_count=projects_evidence[str(project_id)]["win_count"],
            comparison_count=projects_evidence[str(project_id)]["comparison_count"],
            tie_break=tie_breaks.get(str(project_id)),
        )
        for index, project_id in enumerate(ordered)
    ]
