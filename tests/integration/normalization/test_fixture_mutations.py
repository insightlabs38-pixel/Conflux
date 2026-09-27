import math
from collections import Counter

import pytest
from evaluations.normalization import estimate_judge_effects, project_final_score, raw_mean_score
from test_fixture_proof import load_observations


def test_official_fixture_proof_is_repeatable_with_reordered_ballots():
    observations = load_observations()
    original = estimate_judge_effects(observations)
    reordered = estimate_judge_effects(list(reversed(observations)))
    assert original == reordered
    for project_id in {p for _, p, _ in observations}:
        raw = raw_mean_score(observations, project_id)
        adjusted = [
            score - original.judge_effects[j] for j, p, score in observations if p == project_id
        ]
        assert raw is not None
        assert sum(adjusted) / len(adjusted) == pytest.approx(
            project_final_score(original, project_id)
        )


@pytest.mark.parametrize(
    "observations",
    [
        [("a", "p1", 5), ("a", "p2", 5), ("b", "p1", 5), ("b", "p2", 5)],
        [("a", "p1", 0), ("a", "p2", 10), ("b", "p1", 10)],
        [("a", "p1", 0), ("b", "p2", 10)],
        [("a", "p1", 4)],
    ],
)
def test_mutated_score_patterns_stay_finite_and_traceable(observations):
    result = estimate_judge_effects(observations)
    assert result.converged
    for project_id in {p for _, p, _ in observations}:
        assert math.isfinite(project_final_score(result, project_id))
        assert raw_mean_score(observations, project_id) is not None
    assert raw_mean_score(observations, "missing") is None
    assert project_final_score(result, "missing") == result.grand_mean


def test_disconnected_judges_do_not_claim_an_inferred_cross_component_correction():
    observations = [("a", "p1", 0), ("b", "p2", 10)]
    result = estimate_judge_effects(observations)
    assert result.judge_effects == {"a": 0.0, "b": 0.0}
    assert project_final_score(result, "p1") == 0
    assert project_final_score(result, "p2") == 10


def test_official_fixture_with_one_judge_missing_remains_finite():
    observations = load_observations()
    counts = Counter(j for j, _, _ in observations)
    sparse_judge = next(j for j, count in counts.items() if count == 1)
    reduced = [(j, p, score) for j, p, score in observations if j != sparse_judge]
    result = estimate_judge_effects(reduced)
    assert result.converged
    assert all(math.isfinite(score) for score in result.judge_effects.values())
    assert all(math.isfinite(score) for score in result.project_effects.values())
