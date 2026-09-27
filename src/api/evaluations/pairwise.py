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
# VS02: how far above the field's current minimum comparison count a
# candidate may sit and still be offered for an uncertainty-driven pick.
# Keeps coverage from drifting -- a badly under-compared candidate always
# wins over closing in on an already well-compared, merely uncertain pair
# -- while still leaving enough room for the uncertainty signal to matter
# at all (slack 0 would degenerate this back into pure round-robin).
FAIRNESS_SLACK = 1


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


def select_next_pair(candidate_ids, already_compared, comparison_counts, strengths=None):
    """The next pair of candidate ids for a judge to compare (VS02).

    Two-stage, deterministic (ties always broken by ascending-id
    traversal order, never randomly):

    1. Restrict to the "fair pool" -- candidates within `FAIRNESS_SLACK`
       comparisons of the field's current minimum -- so coverage never
       drifts far out of balance.
    2. Within that pool, prefer the not-yet-judged-by-this-judge pair
       whose current Bradley-Terry strengths are closest (the outcome
       least predictable, so the most informative comparison to run
       next). With no `strengths` yet -- nothing has been judged, so
       there is no ranking uncertainty to reduce -- this degrades to the
       same minimal-total-load choice pairwise judging always used.

    Falls back to the full candidate set (still minimal-load, still
    excluding already-compared pairs) only if the fair pool alone has
    nothing left to offer, so a judge is never told "done" while a real
    pair remains, just because that pair happened to sit outside the
    slack window.

    `candidate_ids`: eligible candidates, any order (sorted internally).
    `already_compared`: set of (a, b) tuples in the exact order they were
    stored, matching how the caller compares pairs, unchanged from
    before this batch.
    `comparison_counts`: {candidate_id: int}.
    `strengths`: optional {candidate_id: float}, the latest PairwiseRun.
    """
    ids = sorted(candidate_ids)
    if len(ids) < 2:
        return None
    counts = {c: comparison_counts.get(c, 0) for c in ids}
    min_count = min(counts.values())
    fair_pool = {c for c in ids if counts[c] <= min_count + FAIRNESS_SLACK}

    def best_in(pool):
        best_pair = None
        best_key = None
        for index, a in enumerate(ids):
            if a not in pool:
                continue
            for b in ids[index + 1 :]:
                if b not in pool or (a, b) in already_compared:
                    continue
                if strengths:
                    sa = strengths.get(a, REFERENCE_STRENGTH)
                    sb = strengths.get(b, REFERENCE_STRENGTH)
                    key = (abs(sa - sb) / (sa + sb), counts[a] + counts[b])
                else:
                    key = (counts[a] + counts[b],)
                if best_key is None or key < best_key:
                    best_key = key
                    best_pair = (a, b)
        return best_pair

    return best_in(fair_pool) or best_in(set(ids))


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
