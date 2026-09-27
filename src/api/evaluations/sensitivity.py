"""Read-only ranking what-if calculations over submitted rubric ballots."""

from .normalization import estimate_judge_effects, project_final_score

DEFAULT_RIDGE_LAMBDAS = (0.5, 1.0, 2.0)
DEFAULT_HOLDOUT_COUNTS = (1, 3, 5)


def chronological_observations(plan):
    """Return live ballot scores in deterministic submission order."""
    from .models import Ballot
    from .rubric import weighted_score

    ballots = (
        Ballot.objects.filter(rubric_version__plan=plan, is_calibration=False)
        .order_by("submitted_at", "id")
        .prefetch_related("responses", "rubric_version")
    )
    observations = []
    for ballot in ballots:
        scores = {response.criterion_id: response.score for response in ballot.responses.all()}
        criteria = [c for c in ballot.rubric_version.criteria if c["id"] in scores]
        if not criteria:
            continue
        observations.append((ballot.judge_id, ballot.project_id, weighted_score(criteria, scores)))
    return observations


def _ranked_project_ids(observations, *, ridge_lambda: float) -> list:
    if not observations:
        return []
    result = estimate_judge_effects(observations, ridge_lambda=ridge_lambda)
    project_ids = {project_id for _, project_id, _ in observations}
    return sorted(project_ids, key=lambda p: (-project_final_score(result, p), str(p)))


def ridge_lambda_sensitivity(observations, *, ridge_lambdas=DEFAULT_RIDGE_LAMBDAS) -> dict:
    """Compare judge-bias strengths with the normalization default of 1.0."""
    baseline = _ranked_project_ids(observations, ridge_lambda=1.0)
    scenarios = {}
    for value in ridge_lambdas:
        order = _ranked_project_ids(observations, ridge_lambda=value)
        scenarios[str(value)] = {"order": order, "rank_changed": order != baseline}
    return {"baseline": baseline, "scenarios": scenarios}


def judge_removal_sensitivity(observations, *, ridge_lambda: float = 1.0) -> dict:
    """Compare the current ranking with each judge's ballots removed."""
    baseline = _ranked_project_ids(observations, ridge_lambda=ridge_lambda)
    judge_ids = sorted({judge_id for judge_id, _, _ in observations}, key=str)
    scenarios = {}
    for judge_id in judge_ids:
        without_judge = [o for o in observations if o[0] != judge_id]
        order = _ranked_project_ids(without_judge, ridge_lambda=ridge_lambda)
        scenarios[str(judge_id)] = {"order": order, "rank_changed": order != baseline}
    return {"baseline": baseline, "scenarios": scenarios}


def incompleteness_sensitivity(
    observations, *, ridge_lambda: float = 1.0, holdout_counts=DEFAULT_HOLDOUT_COUNTS
) -> dict:
    """Compare earlier submission prefixes with the current ranking."""
    baseline = _ranked_project_ids(observations, ridge_lambda=ridge_lambda)
    scenarios = {}
    for n in holdout_counts:
        if n <= 0 or n >= len(observations):
            continue
        subset = observations[: len(observations) - n]
        order = _ranked_project_ids(subset, ridge_lambda=ridge_lambda)
        scenarios[str(n)] = {"order": order, "rank_changed": order != baseline}
    return {"baseline": baseline, "scenarios": scenarios}
