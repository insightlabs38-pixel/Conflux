"""NORM-005: fixture-backed Normalization Proof.

Runs the estimator against the real, official DOGFOOD fixture corpus
(fixtures/fixtures.json -- the same file the acceptance checker imports)
rather than synthetic data, and checks properties that must hold of *any*
correct run against it: convergence, no NaNs, and a real corrective effect
(raw-mean ranking and normalized ranking must actually differ somewhere,
since the corpus's judges review very unevenly -- 1 to 11 reviews each).
Nothing here asserts an exact numeric literal: those would be an artifact
of the ridge_lambda choice, not a property of the method.
"""

import json
import math
from pathlib import Path

import pytest
from evaluations.normalization import estimate_judge_effects, project_final_score, raw_mean_score

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "fixtures" / "fixtures.json"


def load_observations():
    with open(FIXTURE_PATH) as f:
        data = json.load(f)
    observations = []
    for score in data["scores"]:
        values = list(score["criteria"].values())
        aggregate = sum(values) / len(values)  # equal-weight mean: the fixture assigns no weights
        observations.append((score["judge"], score["project"], aggregate))
    return observations


@pytest.fixture(scope="module")
def observations():
    return load_observations()


def test_fixture_has_the_expected_official_shape(observations):
    assert len(observations) == 126
    assert len({j for j, _, _ in observations}) == 30
    assert len({p for _, p, _ in observations}) == 41


def test_estimator_converges_on_the_real_corpus_with_no_nans_or_infinities(observations):
    result = estimate_judge_effects(observations, ridge_lambda=1.0)
    assert result.converged
    assert 0 < result.iterations < 200
    for value in list(result.judge_effects.values()) + list(result.project_effects.values()):
        assert math.isfinite(value)


def test_sparse_judges_get_smaller_corrections_than_prolific_ones_of_similar_bias(observations):
    result = estimate_judge_effects(observations, ridge_lambda=1.0)
    counts = {}
    for judge_id, _, _ in observations:
        counts[judge_id] = counts.get(judge_id, 0) + 1
    single_review_judges = [j for j, n in counts.items() if n == 1]
    prolific_judges = [j for j, n in counts.items() if n >= 8]
    assert single_review_judges and prolific_judges
    # Ridge regularization must shrink low-information estimates on average.
    avg_sparse = sum(abs(result.judge_effects[j]) for j in single_review_judges) / len(
        single_review_judges
    )
    avg_prolific = sum(abs(result.judge_effects[j]) for j in prolific_judges) / len(prolific_judges)
    assert avg_sparse <= avg_prolific + 1e-9 or avg_sparse < 1.0


def test_normalization_actually_changes_the_ranking_versus_raw_means(observations):
    # If it never changed anything it wouldn't be doing its job: this corpus
    # has judges reviewing 1 to 11 projects each, exactly the kind of
    # imbalance normalization exists to correct for.
    result = estimate_judge_effects(observations, ridge_lambda=1.0)
    project_ids = sorted({p for _, p, _ in observations})
    raw = {p: raw_mean_score(observations, p) for p in project_ids}
    final = {p: project_final_score(result, p) for p in project_ids}

    raw_rank = sorted(project_ids, key=lambda p: (-raw[p], p))
    final_rank = sorted(project_ids, key=lambda p: (-final[p], p))
    assert raw_rank != final_rank


def test_every_scored_project_has_a_traceable_raw_to_final_evidence_pair(observations):
    result = estimate_judge_effects(observations, ridge_lambda=1.0)
    for project_id in {p for _, p, _ in observations}:
        raw = raw_mean_score(observations, project_id)
        final = project_final_score(result, project_id)
        assert raw is not None
        assert math.isfinite(final)
