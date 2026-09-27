from evaluations.normalization import (
    adjusted_score,
    estimate_judge_effects,
    project_final_score,
    raw_mean_score,
)


def test_empty_observations_return_a_safe_default_without_crashing():
    result = estimate_judge_effects([])
    assert result.judge_effects == {}
    assert result.project_effects == {}
    assert result.converged is True
    assert project_final_score(result, "anything") == 0.0


def test_recovers_relative_project_quality_despite_a_harsh_and_a_lenient_judge():
    # True quality: A > B. Harsh judge always -2, lenient judge always +2.
    observations = [
        ("harsh", "A", 6),
        ("harsh", "B", 4),
        ("lenient", "A", 10),
        ("lenient", "B", 8),
    ]
    result = estimate_judge_effects(observations, ridge_lambda=0.0)
    assert result.converged
    a = project_final_score(result, "A")
    b = project_final_score(result, "B")
    assert a > b
    assert result.judge_effects["harsh"] < 0 < result.judge_effects["lenient"]
    # With no regularization and every judge fully overlapping, bias is
    # fully identified: both judges' adjusted view of the same project
    # should coincide almost exactly.
    assert abs(adjusted_score(result, "harsh", 6) - adjusted_score(result, "lenient", 10)) < 1e-6


def test_deterministic_across_repeated_runs_on_the_same_input():
    observations = [("j1", "p1", 3), ("j1", "p2", 5), ("j2", "p1", 4), ("j2", "p2", 4)]
    first = estimate_judge_effects(observations)
    second = estimate_judge_effects(observations)
    assert first.judge_effects == second.judge_effects
    assert first.project_effects == second.project_effects
    assert first.iterations == second.iterations


def test_project_with_zero_reviews_falls_back_to_grand_mean_not_a_crash():
    observations = [("j1", "p1", 5), ("j2", "p1", 3)]
    result = estimate_judge_effects(observations)
    assert "p2" not in result.review_counts
    assert project_final_score(result, "p2") == result.grand_mean


def test_a_single_review_judge_and_a_constant_score_judge_are_flagged_low_information():
    observations = [
        ("sparse", "p1", 5),
        ("constant", "p1", 4),
        ("constant", "p2", 4),
        ("constant", "p3", 4),
        ("normal", "p1", 3),
        ("normal", "p2", 5),
        ("normal", "p3", 2),
    ]
    result = estimate_judge_effects(observations)
    assert set(result.low_information_judges) == {"sparse", "constant"}
    assert "normal" not in result.low_information_judges


def test_ridge_regularization_shrinks_a_sparsely_reviewed_judges_effect():
    # Both judges are equally "harsh" (-3 vs the other judges' scores on
    # shared projects), but "sparse" only ever reviewed one project.
    dense_observations = [
        ("dense", "p1", 2),
        ("dense", "p2", 2),
        ("dense", "p3", 2),
        ("dense", "p4", 2),
        ("other", "p1", 5),
        ("other", "p2", 5),
        ("other", "p3", 5),
        ("other", "p4", 5),
    ]
    sparse_observations = dense_observations + [("sparse", "p1", 2)]
    dense_result = estimate_judge_effects(dense_observations)
    sparse_result = estimate_judge_effects(sparse_observations)
    assert abs(sparse_result.judge_effects["sparse"]) < abs(dense_result.judge_effects["dense"])


def test_raw_mean_score_matches_a_hand_computed_average():
    observations = [("j1", "p1", 2), ("j2", "p1", 4), ("j1", "p2", 10)]
    assert raw_mean_score(observations, "p1") == 3
    assert raw_mean_score(observations, "missing") is None
