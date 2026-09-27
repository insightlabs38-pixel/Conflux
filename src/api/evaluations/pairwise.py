"""Bradley-Terry strength estimator for pairwise judging (S01).

Model: P(i beats j) = strength_i / (strength_i + strength_j), each
strength_i > 0. Solved by the classical Newman/Hunter MM (minorization-
maximization) fixed-point iteration: deterministic, fixed sorted id order,
no random initialization -- the same "same input, same output, always"
property NORM-001's Gauss-Seidel solver has (see normalization.py).

`prior_games` regularizes every candidate against a fixed virtual
opponent of strength 1.0 (half win, half loss): a candidate with zero, or
entirely one-sided, real comparisons gets a finite, cautious strength near
the field average instead of drifting to 0 or infinity. This also fixes
the scale: Bradley-Terry strengths are only identifiable up to a common
multiplicative constant, and anchoring every candidate against the same
fixed-strength virtual opponent removes that free parameter without a
separate normalization step.
"""

from collections import defaultdict
from dataclasses import dataclass

REFERENCE_STRENGTH = 1.0


@dataclass(frozen=True)
class PairwiseResult:
    strengths: dict  # project_id -> positive float, prior-regularized
    win_counts: dict  # project_id -> raw weighted win count observed
    comparison_counts: dict  # project_id -> weighted comparisons involving this project
    iterations: int
    converged: bool
    prior_games: float


def estimate_strengths(
    observations, *, prior_games: float = 2.0, max_iterations: int = 1000, tol: float = 1e-9
) -> PairwiseResult:
    """`observations`: iterable of (winner_id, loser_id, weight). A declared
    tie is two entries, (a, b, 0.5) and (b, a, 0.5) -- half a win each way,
    still real evidence the two candidates are close in strength rather
    than evidence that gets dropped.
    """
    obs = list(observations)
    project_ids = sorted({p for winner, loser, _ in obs for p in (winner, loser)}, key=str)
    if not project_ids:
        return PairwiseResult({}, {}, {}, 0, True, prior_games)

    win_counts = defaultdict(float)
    comparison_counts = defaultdict(float)
    pair_games = defaultdict(float)  # (a, b) with str(a) <= str(b) -> weighted games
    for winner_id, loser_id, weight in obs:
        win_counts[winner_id] += weight
        comparison_counts[winner_id] += weight
        comparison_counts[loser_id] += weight
        key = tuple(sorted((winner_id, loser_id), key=str))
        pair_games[key] += weight

    opponents = defaultdict(list)  # project_id -> [(other_id, weighted_games), ...]
    for (a, b), n in pair_games.items():
        opponents[a].append((b, n))
        opponents[b].append((a, n))

    strength = dict.fromkeys(project_ids, 1.0)
    converged = False
    iteration = 0
    for iteration in range(1, max_iterations + 1):
        new_strength = {}
        for p in project_ids:
            numerator = win_counts[p] + prior_games / 2
            denominator = prior_games / (strength[p] + REFERENCE_STRENGTH)
            for other_id, n_games in opponents[p]:
                denominator += n_games / (strength[p] + strength[other_id])
            new_strength[p] = numerator / denominator if denominator > 0 else strength[p]
        delta = max(abs(new_strength[p] - strength[p]) for p in project_ids)
        strength = new_strength
        if delta < tol:
            converged = True
            break

    return PairwiseResult(
        strengths=strength,
        win_counts={p: win_counts.get(p, 0.0) for p in project_ids},
        comparison_counts={p: comparison_counts.get(p, 0.0) for p in project_ids},
        iterations=iteration,
        converged=converged,
        prior_games=prior_games,
    )


def comparison_observations(plan):
    """[(winner_id, loser_id, weight), ...] for every PairwiseComparison ever
    recorded under `plan`.
    """
    observations = []
    for comparison in plan.pairwise_comparisons.all():
        if comparison.winner_id is None:
            observations.append((comparison.project_a_id, comparison.project_b_id, 0.5))
            observations.append((comparison.project_b_id, comparison.project_a_id, 0.5))
        else:
            loser_id = (
                comparison.project_b_id
                if comparison.winner_id == comparison.project_a_id
                else comparison.project_a_id
            )
            observations.append((comparison.winner_id, loser_id, 1.0))
    return observations


def run(plan, *, prior_games: float = 2.0):
    """Compute + freeze a new PairwiseRun for `plan` (S01, the pairwise
    analogue of normalization.run). Caller wraps this in a transaction and
    records an audit event (see evaluations.views.PairwiseRunListView).
    """
    from .models import PairwiseRun

    observations = comparison_observations(plan)
    result = estimate_strengths(observations, prior_games=prior_games)
    project_ids = sorted(result.strengths, key=str)
    next_number = (
        plan.pairwise_runs.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    evidence = {
        "projects": {
            str(project_id): {
                "strength": result.strengths[project_id],
                "win_count": result.win_counts.get(project_id, 0.0),
                "comparison_count": result.comparison_counts.get(project_id, 0.0),
            }
            for project_id in project_ids
        },
    }
    return PairwiseRun.objects.create(
        plan=plan,
        number=next_number,
        prior_games=prior_games,
        iterations=result.iterations,
        converged=result.converged,
        evidence=evidence,
    )
