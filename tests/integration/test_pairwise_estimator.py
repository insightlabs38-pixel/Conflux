from evaluations.pairwise import estimate_strengths


def test_empty_observations_return_a_safe_default_without_crashing():
    result = estimate_strengths([])
    assert result.strengths == {}
    assert result.converged is True
    assert result.iterations == 0


def test_recovers_relative_strength_from_consistent_head_to_head_wins():
    # A beats everyone, B beats C, C never wins.
    observations = [
        ("A", "B", 1.0),
        ("A", "C", 1.0),
        ("B", "C", 1.0),
    ]
    result = estimate_strengths(observations, prior_games=1.0)
    assert result.converged
    assert result.strengths["A"] > result.strengths["B"] > result.strengths["C"]


def test_deterministic_across_repeated_runs_on_the_same_input():
    observations = [("A", "B", 1.0), ("B", "C", 1.0), ("C", "A", 1.0)]
    first = estimate_strengths(observations)
    second = estimate_strengths(observations)
    assert first.strengths == second.strengths
    assert first.iterations == second.iterations


def test_a_tie_contributes_half_a_win_each_way_and_pulls_strengths_together():
    observations = [("A", "B", 0.5), ("B", "A", 0.5)]
    result = estimate_strengths(observations, prior_games=1.0)
    assert result.converged
    assert abs(result.strengths["A"] - result.strengths["B"]) < 1e-9


def test_an_undefeated_candidate_gets_a_finite_regularized_strength_not_infinity():
    # A beats B every time they meet; with no prior this would drive A's
    # strength to infinity and B's to zero -- the whole point of anchoring
    # every candidate against a fixed virtual opponent (see pairwise.py).
    observations = [("A", "B", 1.0)] * 10
    result = estimate_strengths(observations, prior_games=2.0)
    assert result.converged
    assert 0 < result.strengths["B"] < result.strengths["A"] < float("inf")


def test_a_candidate_with_zero_comparisons_never_appears_in_the_result():
    observations = [("A", "B", 1.0)]
    result = estimate_strengths(observations)
    assert set(result.strengths) == {"A", "B"}


def test_win_and_comparison_counts_are_raw_not_regularized():
    observations = [("A", "B", 1.0), ("A", "C", 1.0), ("B", "C", 1.0)]
    result = estimate_strengths(observations, prior_games=5.0)
    assert result.win_counts == {"A": 2.0, "B": 1.0, "C": 0.0}
    assert result.comparison_counts == {"A": 2.0, "B": 2.0, "C": 2.0}
