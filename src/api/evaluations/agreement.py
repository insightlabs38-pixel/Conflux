"""Inter-rater agreement analytics (S03): real criterion-level score
dispersion and judge-pair ranking correlation, computed honestly -- a
statistic backed by too little data is reported as absent rather than a
confident-looking number computed from noise. Always computed live from
current ballots (never persisted as a frozen "run" like NormalizationRun/
PairwiseRun): this is an exploratory diagnostic, not evidence a published
result is drawn from, so there is nothing here that needs NORM-004-style
reproducibility.
"""

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean, pstdev

MIN_JUDGES_FOR_DISPERSION = 2
MIN_SHARED_CANDIDATES_FOR_RANK_AGREEMENT = 3


@dataclass(frozen=True)
class CriterionDisagreement:
    project_id: object
    criterion_id: str
    scores: dict  # judge_id -> score
    mean: float
    range: float
    stdev: float


def criterion_disagreement(responses) -> list[CriterionDisagreement]:
    """`responses`: iterable of (judge_id, project_id, criterion_id, score).

    Only (project, criterion) pairs scored by at least
    `MIN_JUDGES_FOR_DISPERSION` distinct judges are returned -- a single
    judge's score has nothing to disagree with, and reporting a fabricated
    zero there would look like measured agreement rather than absent data.
    """
    grouped = defaultdict(dict)
    for judge_id, project_id, criterion_id, score in responses:
        grouped[(project_id, criterion_id)][judge_id] = score

    results = [
        CriterionDisagreement(
            project_id=project_id,
            criterion_id=criterion_id,
            scores=dict(scores),
            mean=mean(scores.values()),
            range=max(scores.values()) - min(scores.values()),
            stdev=pstdev(scores.values()),
        )
        for (project_id, criterion_id), scores in grouped.items()
        if len(scores) >= MIN_JUDGES_FOR_DISPERSION
    ]
    return sorted(results, key=lambda r: (-r.range, str(r.project_id), r.criterion_id))


@dataclass(frozen=True)
class RankAgreement:
    judge_a: object
    judge_b: object
    shared_candidates: int
    tau: float | None  # None below MIN_SHARED_CANDIDATES_FOR_RANK_AGREEMENT


def _kendall_tau(a_scores: dict, b_scores: dict, shared_ids: list) -> float:
    """Kendall's tau-b over `shared_ids`, ranking each judge by their own
    raw scores (ties allowed on either side). Returns 0.0 in the
    degenerate case where one judge's shared scores are all equal (no
    ranking to correlate against) rather than dividing by zero.
    """
    concordant = discordant = tied_a = tied_b = 0
    for i in range(len(shared_ids)):
        for j in range(i + 1, len(shared_ids)):
            p, q = shared_ids[i], shared_ids[j]
            da = a_scores[p] - a_scores[q]
            db = b_scores[p] - b_scores[q]
            if da == 0 and db == 0:
                continue
            if da == 0:
                tied_a += 1
            elif db == 0:
                tied_b += 1
            elif (da > 0) == (db > 0):
                concordant += 1
            else:
                discordant += 1
    denominator = ((concordant + discordant + tied_a) * (concordant + discordant + tied_b)) ** 0.5
    return (concordant - discordant) / denominator if denominator else 0.0


def pairwise_rank_agreement(judge_scores: dict) -> list[RankAgreement]:
    """`judge_scores`: {judge_id: {project_id: score}} -- each judge's own
    raw scores for the candidates they reviewed (see judge_weighted_scores).
    Every judge pair is reported (so a thin pool is visible), but `tau` is
    only a number once the pair shares at least
    `MIN_SHARED_CANDIDATES_FOR_RANK_AGREEMENT` candidates; below that it is
    `None` rather than a coefficient computed from too little to mean
    anything (with 2 shared candidates, tau is always exactly +-1 or 0,
    which is not a meaningful correlation).
    """
    judges = sorted(judge_scores, key=str)
    results = []
    for i in range(len(judges)):
        for j in range(i + 1, len(judges)):
            judge_a, judge_b = judges[i], judges[j]
            shared = sorted(set(judge_scores[judge_a]) & set(judge_scores[judge_b]), key=str)
            tau = (
                _kendall_tau(judge_scores[judge_a], judge_scores[judge_b], shared)
                if len(shared) >= MIN_SHARED_CANDIDATES_FOR_RANK_AGREEMENT
                else None
            )
            results.append(RankAgreement(judge_a, judge_b, len(shared), tau))
    return results


def criterion_responses(plan):
    """[(judge_id, project_id, criterion_id, score), ...] for every live
    (non-calibration) ballot response ever cast under `plan`.
    """
    from .models import Ballot

    responses = []
    ballots = Ballot.objects.filter(
        rubric_version__plan=plan, is_calibration=False
    ).prefetch_related("responses")
    for ballot in ballots:
        for response in ballot.responses.all():
            responses.append(
                (ballot.judge_id, ballot.project_id, response.criterion_id, response.score)
            )
    return responses


def judge_weighted_scores(plan) -> dict:
    """{judge_id: {project_id: weighted_score}}, reusing
    scoring.ballot_observations so this always ranks by the same
    frozen-rubric-weight aggregate score normalization does (NORM-002).
    """
    from .scoring import ballot_observations

    scores = defaultdict(dict)
    for judge_id, project_id, score in ballot_observations(plan):
        scores[judge_id][project_id] = score
    return dict(scores)
