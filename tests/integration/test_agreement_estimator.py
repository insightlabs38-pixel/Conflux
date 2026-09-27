from evaluations.agreement import criterion_disagreement, pairwise_rank_agreement


def test_a_single_judges_score_produces_no_disagreement_entry():
    responses = [("j1", "p1", "impact", 8)]
    assert criterion_disagreement(responses) == []


def test_two_judges_scoring_the_same_criterion_produce_real_dispersion():
    responses = [("j1", "p1", "impact", 8), ("j2", "p1", "impact", 4)]
    results = criterion_disagreement(responses)
    assert len(results) == 1
    result = results[0]
    assert result.scores == {"j1": 8, "j2": 4}
    assert result.mean == 6
    assert result.range == 4
    assert result.stdev == 2.0


def test_results_are_sorted_by_descending_range():
    responses = [
        ("j1", "p1", "impact", 5),
        ("j2", "p1", "impact", 5),  # range 0
        ("j1", "p2", "impact", 10),
        ("j2", "p2", "impact", 0),  # range 10
    ]
    results = criterion_disagreement(responses)
    assert [r.project_id for r in results] == ["p2", "p1"]


def test_identical_rankings_have_perfect_positive_tau():
    judge_scores = {
        "j1": {"p1": 1, "p2": 2, "p3": 3},
        "j2": {"p1": 10, "p2": 20, "p3": 30},
    }
    results = pairwise_rank_agreement(judge_scores)
    assert len(results) == 1
    assert results[0].shared_candidates == 3
    assert results[0].tau == 1.0


def test_reversed_rankings_have_perfect_negative_tau():
    judge_scores = {
        "j1": {"p1": 1, "p2": 2, "p3": 3},
        "j2": {"p1": 30, "p2": 20, "p3": 10},
    }
    results = pairwise_rank_agreement(judge_scores)
    assert results[0].tau == -1.0


def test_fewer_than_the_minimum_shared_candidates_reports_no_tau_not_a_fake_one():
    judge_scores = {"j1": {"p1": 1, "p2": 2}, "j2": {"p1": 10, "p2": 5}}
    results = pairwise_rank_agreement(judge_scores)
    assert results[0].shared_candidates == 2
    assert results[0].tau is None


def test_a_judge_pair_with_no_shared_candidates_is_still_reported():
    judge_scores = {"j1": {"p1": 1}, "j2": {"p2": 1}}
    results = pairwise_rank_agreement(judge_scores)
    assert len(results) == 1
    assert results[0].shared_candidates == 0
    assert results[0].tau is None


def test_a_constant_judge_against_a_varying_judge_yields_zero_not_a_crash():
    judge_scores = {
        "j1": {"p1": 5, "p2": 5, "p3": 5},
        "j2": {"p1": 1, "p2": 2, "p3": 3},
    }
    results = pairwise_rank_agreement(judge_scores)
    assert results[0].tau == 0.0
