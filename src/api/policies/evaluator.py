"""Typed, bounded policy AST and evaluator (POL-001).

A policy is plain JSON — safe to store, transmit, and author without ever
handing anything an interpreter: no eval/exec, no calling into JS/Python/
SQL. Every node has an explicit, closed set of operators, and every leaf
names a fact that the *caller* must supply. Depth and node count are
capped so a pathological policy can't blow the stack or take unbounded
time to evaluate.

Fail-closed is the caller's contract, not a default this module quietly
applies: `evaluate` raises PolicyError on anything malformed, unknown, or
missing (an unrecognized operator, a fact the caller didn't supply,
excessive depth/size) rather than guessing a value. `is_allowed` is the
fail-closed wrapper — any PolicyError becomes `False` — for gating a
protected action (POL-002); code that's authoring or testing a policy
should call `evaluate` directly and see the real error.
"""

from datetime import datetime

from django.utils.dateparse import parse_datetime

MAX_DEPTH = 10
MAX_NODES = 200

_BOOLEAN_OPS = {"and", "or"}
_COMPARISON_OPS = {"eq", "ne", "gt", "gte", "lt", "lte"}
_MEMBERSHIP_OPS = {"in", "not_in"}
OPERATORS = _BOOLEAN_OPS | _COMPARISON_OPS | _MEMBERSHIP_OPS | {"not", "true", "false"}


class PolicyError(ValueError):
    pass


def _coerce_for_comparison(fact_value, raw_value):
    """`raw_value` comes from JSON, so a datetime fact is compared against
    an ISO string that needs parsing; anything else compares as-is.
    """
    if isinstance(fact_value, datetime):
        parsed = parse_datetime(raw_value) if isinstance(raw_value, str) else None
        if parsed is None:
            raise PolicyError(f"Not a valid ISO 8601 timestamp for comparison: {raw_value!r}")
        return parsed
    return raw_value


def _fact(node, facts):
    name = node.get("fact")
    if not isinstance(name, str):
        raise PolicyError("A comparison node needs a string 'fact'.")
    if name not in facts:
        # Deliberately not `facts.get(name)`: an unsupplied fact is
        # "unknown", not "falsy", and this is the fail-closed boundary.
        raise PolicyError(f"Unknown fact: {name!r}")
    return facts[name]


def evaluate(node, facts, *, _depth=0, _budget=None):
    """Evaluate a policy AST node to a bool. Raises PolicyError on any
    malformed node, unknown operator/fact, or depth/size overrun.
    """
    if _budget is None:
        _budget = [MAX_NODES]
    _budget[0] -= 1
    if _budget[0] < 0:
        raise PolicyError(f"Policy AST exceeds the maximum of {MAX_NODES} nodes.")
    if _depth > MAX_DEPTH:
        raise PolicyError(f"Policy AST exceeds the maximum depth of {MAX_DEPTH}.")
    if not isinstance(node, dict):
        raise PolicyError(f"Malformed policy node (expected an object): {node!r}")

    op = node.get("op")
    if op not in OPERATORS:
        raise PolicyError(f"Unknown policy operator: {op!r}")

    if op == "true":
        return True
    if op == "false":
        return False

    if op == "not":
        args = node.get("args")
        if not isinstance(args, list) or len(args) != 1:
            raise PolicyError("'not' takes exactly one argument.")
        return not evaluate(args[0], facts, _depth=_depth + 1, _budget=_budget)

    if op in _BOOLEAN_OPS:
        args = node.get("args")
        if not isinstance(args, list) or not args:
            raise PolicyError(f"'{op}' needs a nonempty list of arguments.")
        results = (evaluate(a, facts, _depth=_depth + 1, _budget=_budget) for a in args)
        return any(results) if op == "or" else all(results)

    if op in _COMPARISON_OPS:
        fact_value = _fact(node, facts)
        raw_value = node.get("value")
        value = _coerce_for_comparison(fact_value, raw_value)
        try:
            if op == "eq":
                return fact_value == value
            if op == "ne":
                return fact_value != value
            if op == "gt":
                return fact_value > value
            if op == "gte":
                return fact_value >= value
            if op == "lt":
                return fact_value < value
            return fact_value <= value  # lte
        except TypeError as exc:
            raise PolicyError(f"Cannot compare {fact_value!r} and {value!r}.") from exc

    # op in _MEMBERSHIP_OPS
    fact_value = _fact(node, facts)
    options = node.get("value")
    if not isinstance(options, list):
        raise PolicyError(f"'{op}' needs a list 'value'.")
    return (fact_value in options) if op == "in" else (fact_value not in options)


def is_allowed(node, facts):
    """Fail-closed entrypoint for gating a protected action: any malformed
    or unresolvable policy denies rather than raising.
    """
    try:
        return bool(evaluate(node, facts))
    except PolicyError:
        return False
