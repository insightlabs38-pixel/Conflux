"""Read-only diagnostics for one frozen rubric version and its ballots."""

from collections import defaultdict
from statistics import pvariance

from .normalization import estimate_judge_effects, project_final_score
from .rubric import weighted_score

DEFAULT_FACTORS = (0.5, 1.5)


def version_samples(version):
    from .models import Ballot

    ballots = (
        Ballot.objects.filter(rubric_version=version, is_calibration=False)
        .order_by("id")
        .prefetch_related("responses")
    )
    return [
        (
            ballot.judge_id,
            ballot.project_id,
            {response.criterion_id: response.score for response in ballot.responses.all()},
        )
        for ballot in ballots
    ]


def _ranking(criteria, samples):
    observations = []
    for judge_id, project_id, scores in samples:
        answered = [criterion for criterion in criteria if criterion["id"] in scores]
        if answered:
            observations.append((judge_id, project_id, weighted_score(answered, scores)))
    if not observations:
        return []
    result = estimate_judge_effects(observations)
    project_ids = {project_id for _, project_id, _ in observations}
    return sorted(project_ids, key=lambda p: (-project_final_score(result, p), p))


def analyze(criteria, samples, *, factors=DEFAULT_FACTORS):
    """Measure scale use and rank shifts without changing published evidence."""
    baseline = _ranking(criteria, samples)
    positions = {project_id: rank for rank, project_id in enumerate(baseline)}
    values = defaultdict(list)
    components = defaultdict(list)
    for _, _, scores in samples:
        answered = [criterion for criterion in criteria if criterion["id"] in scores]
        if not answered:
            continue
        total_weight = sum(criterion["weight"] for criterion in answered)
        for criterion in answered:
            criterion_id = criterion["id"]
            values[criterion_id].append(scores[criterion_id])
            components[criterion_id].append(
                scores[criterion_id] * criterion["weight"] / total_weight
            )
    spread_variances = {
        criterion["id"]: pvariance(components[criterion["id"]])
        if components[criterion["id"]]
        else 0.0
        for criterion in criteria
    }
    total_spread_variance = sum(spread_variances.values())
    total_weight = sum(criterion["weight"] for criterion in criteria)
    diagnostics = []
    for criterion in criteria:
        criterion_id = criterion["id"]
        observed = values[criterion_id]
        weight_share = criterion["weight"] / total_weight
        spread_share = (
            spread_variances[criterion_id] / total_spread_variance
            if total_spread_variance
            else None
        )
        scenarios = []
        for factor in factors:
            changed = [
                {**item, "weight": item["weight"] * factor} if item["id"] == criterion_id else item
                for item in criteria
            ]
            order = _ranking(changed, samples)
            scenarios.append(
                {
                    "factor": factor,
                    "order": order,
                    "rank_changed_count": sum(
                        positions.get(project_id) != index for index, project_id in enumerate(order)
                    ),
                    "top_changed": bool(baseline and order and baseline[0] != order[0]),
                }
            )
        diagnostics.append(
            {
                "criterion_id": criterion_id,
                "name": criterion["name"],
                "weight_share": weight_share,
                "response_count": len(observed),
                "missing_count": len(samples) - len(observed),
                "mean": sum(observed) / len(observed) if observed else None,
                "variance": pvariance(observed) if observed else None,
                "scale_use": (
                    (max(observed) - min(observed))
                    / (criterion["max_score"] - criterion["min_score"])
                    if observed
                    else None
                ),
                "at_min_count": sum(score == criterion["min_score"] for score in observed),
                "at_max_count": sum(score == criterion["max_score"] for score in observed),
                "spread_share": spread_share,
                "dominates": weight_share > 0.5
                or (spread_share is not None and spread_share > 0.5),
                "weight_scenarios": scenarios,
            }
        )
    return {"ballot_count": len(samples), "baseline": baseline, "criteria": diagnostics}
