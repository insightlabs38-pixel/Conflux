"""Regularized additive judge-effect estimator (NORM-001).

Model: observed_score(j, p) ~= grand_mean + project_effect[p] + judge_effect[j].
`project_effect` is left unregularized -- it's the quality signal the whole
system exists to recover, so nothing should shrink it toward the mean.
`judge_effect` is ridge-regularized toward 0: a judge with few reviews, or
one who (per a disconnected assignment graph -- see connectivity.py) has
little information tying them to the rest of the pool, gets a small,
cautious correction instead of an overconfident one built on noise.

Solved by deterministic Gauss-Seidel alternation between the two effects:
sorted judge/project ids, a fixed iteration cap, and a tolerance-based
early stop, so the same observations always produce the same result --
no random initialization, no solver-dependent floating point drift.
"""

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NormalizationResult:
    grand_mean: float
    judge_effects: dict
    project_effects: dict
    review_counts: dict  # project_id -> number of ballots observed
    iterations: int
    converged: bool
    low_information_judges: list = field(default_factory=list)


def estimate_judge_effects(
    observations, *, ridge_lambda: float = 1.0, max_iterations: int = 200, tol: float = 1e-9
) -> NormalizationResult:
    """`observations`: iterable of (judge_id, project_id, score).

    Judge/project ids may be any hashable (real Ballot rows use integer pks;
    the fixture-backed proof in NORM-005 uses the fixture's string ids
    directly) -- the math doesn't care what the identifiers are.
    """
    obs = list(observations)
    if not obs:
        return NormalizationResult(0.0, {}, {}, {}, 0, True)

    grand_mean = sum(score for _, _, score in obs) / len(obs)

    by_judge = defaultdict(list)
    by_project = defaultdict(list)
    for judge_id, project_id, score in obs:
        by_judge[judge_id].append((project_id, score))
        by_project[project_id].append((judge_id, score))

    judge_ids = sorted(by_judge, key=str)
    project_ids = sorted(by_project, key=str)
    judge_effect = dict.fromkeys(judge_ids, 0.0)
    project_effect = dict.fromkeys(project_ids, 0.0)

    converged = False
    iteration = 0
    for iteration in range(1, max_iterations + 1):
        new_project_effect = {
            p: sum(score - grand_mean - judge_effect[j] for j, score in by_project[p])
            / len(by_project[p])
            for p in project_ids
        }
        new_judge_effect = {
            j: sum(score - grand_mean - new_project_effect[p] for p, score in by_judge[j])
            / (len(by_judge[j]) + ridge_lambda)
            for j in judge_ids
        }
        delta = max(
            max((abs(new_project_effect[p] - project_effect[p]) for p in project_ids), default=0.0),
            max((abs(new_judge_effect[j] - judge_effect[j]) for j in judge_ids), default=0.0),
        )
        project_effect, judge_effect = new_project_effect, new_judge_effect
        if delta < tol:
            converged = True
            break

    review_counts = {p: len(by_project[p]) for p in project_ids}
    low_information = sorted(
        (
            j
            for j in judge_ids
            if len(by_judge[j]) <= 1 or len({round(s, 9) for _, s in by_judge[j]}) <= 1
        ),
        key=str,
    )
    return NormalizationResult(
        grand_mean,
        judge_effect,
        project_effect,
        review_counts,
        iteration,
        converged,
        low_information,
    )


def adjusted_score(result: NormalizationResult, judge_id, raw_score: float) -> float:
    """One ballot's score with that judge's estimated bias removed."""
    return raw_score - result.judge_effects.get(judge_id, 0.0)


def project_final_score(result: NormalizationResult, project_id) -> float:
    """A project's normalized final score: grand mean plus its estimated
    effect. Falls back to the grand mean for a project with zero
    observations (no evidence -> assume average, never a crash or None).
    """
    return result.grand_mean + result.project_effects.get(project_id, 0.0)


def raw_mean_score(observations, project_id) -> float | None:
    """The naive, unadjusted average for one project -- what NORM-004's
    evidence calls "raw", to trace against "adjusted"/"final".
    """
    scores = [score for _, p, score in observations if p == project_id]
    return sum(scores) / len(scores) if scores else None


def run(plan, *, ridge_lambda: float = 1.0):
    """Compute + freeze a new NormalizationRun for `plan` (NORM-004). Caller
    wraps this in a transaction and records an audit event (see
    evaluations.views.NormalizationRunView), the same shape as
    assignment.activate().
    """
    from .models import NormalizationRun
    from .scoring import ballot_observations

    observations = ballot_observations(plan)
    result = estimate_judge_effects(observations, ridge_lambda=ridge_lambda)
    project_ids = sorted({p for _, p, _ in observations}, key=str)
    next_number = (
        plan.normalization_runs.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    evidence = {
        "review_counts": {str(k): v for k, v in result.review_counts.items()},
        "judge_effects": {str(k): v for k, v in sorted(result.judge_effects.items(), key=str)},
        "low_information_judges": [str(j) for j in result.low_information_judges],
        "projects": {
            str(project_id): {
                "raw": raw_mean_score(observations, project_id),
                "final": project_final_score(result, project_id),
            }
            for project_id in project_ids
        },
    }
    normalization_run = NormalizationRun.objects.create(
        plan=plan,
        number=next_number,
        ridge_lambda=ridge_lambda,
        iterations=result.iterations,
        converged=result.converged,
        grand_mean=result.grand_mean,
        evidence=evidence,
    )
    return normalization_run
