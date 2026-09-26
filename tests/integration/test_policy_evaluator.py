from datetime import UTC, datetime

import pytest
from policies.evaluator import MAX_DEPTH, PolicyError, evaluate, is_allowed


def test_true_and_false_constants():
    assert evaluate({"op": "true"}, {}) is True
    assert evaluate({"op": "false"}, {}) is False


def test_eq_and_ne():
    facts = {"role": "organizer"}
    assert evaluate({"op": "eq", "fact": "role", "value": "organizer"}, facts) is True
    assert evaluate({"op": "ne", "fact": "role", "value": "judge"}, facts) is True
    assert evaluate({"op": "eq", "fact": "role", "value": "judge"}, facts) is False


def test_in_and_not_in():
    facts = {"role": "judge"}
    assert evaluate({"op": "in", "fact": "role", "value": ["organizer", "judge"]}, facts) is True
    assert evaluate({"op": "not_in", "fact": "role", "value": ["organizer"]}, facts) is True


def test_and_or_not_compose():
    facts = {"role": "organizer", "is_owner": False}
    node = {
        "op": "or",
        "args": [
            {"op": "eq", "fact": "role", "value": "organizer"},
            {"op": "eq", "fact": "is_owner", "value": True},
        ],
    }
    assert evaluate(node, facts) is True
    assert evaluate({"op": "not", "args": [node]}, facts) is False


def test_temporal_comparison_parses_iso_value_against_a_datetime_fact():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    node = {"op": "gte", "fact": "now", "value": "2026-01-01T00:00:00Z"}
    assert evaluate(node, {"now": now}) is True
    node_future = {"op": "lt", "fact": "now", "value": "2026-01-01T00:00:00Z"}
    assert evaluate(node_future, {"now": now}) is False


def test_unknown_operator_raises():
    with pytest.raises(PolicyError, match="Unknown policy operator"):
        evaluate({"op": "shell_exec", "args": []}, {})


def test_unknown_fact_raises_rather_than_treating_as_falsy():
    with pytest.raises(PolicyError, match="Unknown fact"):
        evaluate({"op": "eq", "fact": "nonexistent", "value": 1}, {"role": "organizer"})


def test_malformed_node_raises():
    with pytest.raises(PolicyError):
        evaluate("not-a-dict", {})
    with pytest.raises(PolicyError):
        evaluate({"op": "and", "args": "not-a-list"}, {})


def test_excessive_depth_is_rejected():
    node = {"op": "true"}
    for _ in range(MAX_DEPTH + 5):
        node = {"op": "not", "args": [node]}
    with pytest.raises(PolicyError, match="maximum depth"):
        evaluate(node, {})


def test_excessive_node_count_is_rejected():
    # "and" with every child true: all() can't short-circuit, so every
    # child actually gets evaluated and the budget is genuinely exhausted.
    node = {"op": "and", "args": [{"op": "true"} for _ in range(500)]}
    with pytest.raises(PolicyError, match="maximum"):
        evaluate(node, {})


def test_incomparable_types_raise():
    with pytest.raises(PolicyError, match="Cannot compare"):
        evaluate({"op": "gt", "fact": "n", "value": "not-a-number"}, {"n": 5})


def test_is_allowed_fails_closed_on_any_policy_error():
    assert is_allowed({"op": "eq", "fact": "missing", "value": 1}, {}) is False
    assert is_allowed({"op": "bogus"}, {}) is False


def test_is_allowed_returns_the_real_result_when_the_policy_is_valid():
    assert is_allowed({"op": "true"}, {}) is True
    assert is_allowed({"op": "eq", "fact": "role", "value": "judge"}, {"role": "judge"}) is True
    assert (
        is_allowed({"op": "eq", "fact": "role", "value": "judge"}, {"role": "organizer"}) is False
    )
