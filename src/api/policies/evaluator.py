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


def _trace_value(value):
    return value.isoformat() if isinstance(value, datetime) else value


def _mark_skipped(entry, node, path):
    args = node.get("args") if isinstance(node, dict) else None
    if not isinstance(args, list):
        return
    seen = {child["path"][-1] for child in entry["children"]}
    for index, child in enumerate(args):
        if index not in seen:
            entry["children"].append(
                {
                    "path": [*path, index],
                    "op": child.get("op") if isinstance(child, dict) else None,
                    "status": "skipped",
                }
            )


def evaluate(node, facts, *, _depth=0, _budget=None, _trace=None, _path=()):
    """Evaluate a policy AST node to a bool. Raises PolicyError on any
    malformed node, unknown operator/fact, or depth/size overrun.
    """
    entry = None
    if _trace is not None:
        entry = {"path": list(_path), "op": node.get("op") if isinstance(node, dict) else None}
        if isinstance(node, dict) and isinstance(node.get("fact"), str):
            entry["fact"] = node["fact"]
            entry["expected"] = node.get("value")
            if node["fact"] in facts:
                entry["actual"] = _trace_value(facts[node["fact"]])
        entry["children"] = []
        _trace.append(entry)
    try:
        result = _evaluate_node(
            node, facts, _depth=_depth, _budget=_budget, _trace=entry, _path=_path
        )
    except PolicyError as exc:
        if entry is not None:
            entry["status"] = "error"
            entry["error"] = str(exc)
            _mark_skipped(entry, node, _path)
        raise
    if entry is not None:
        entry["status"] = "evaluated"
        entry["result"] = result
        _mark_skipped(entry, node, _path)
    return result


def _evaluate_node(node, facts, *, _depth, _budget, _trace, _path):
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
        return not evaluate(
            args[0],
            facts,
            _depth=_depth + 1,
            _budget=_budget,
            _trace=_trace["children"] if _trace is not None else None,
            _path=(*_path, 0),
        )

    if op in _BOOLEAN_OPS:
        args = node.get("args")
        if not isinstance(args, list) or not args:
            raise PolicyError(f"'{op}' needs a nonempty list of arguments.")
        results = (
            evaluate(
                arg,
                facts,
                _depth=_depth + 1,
                _budget=_budget,
                _trace=_trace["children"] if _trace is not None else None,
                _path=(*_path, index),
            )
            for index, arg in enumerate(args)
        )
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


def validate_structure(node, *, _depth=0, _budget=None):
    """Check a policy AST is well-formed (operators, shapes, depth/size)
    without evaluating it — an author saving a Policy (POL-002) hasn't
    supplied real facts yet, so the "unknown fact" check in `evaluate`
    doesn't apply here; everything else does. Raises PolicyError, returns
    nothing on success.
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
    if op in ("true", "false"):
        return

    if op == "not":
        args = node.get("args")
        if not isinstance(args, list) or len(args) != 1:
            raise PolicyError("'not' takes exactly one argument.")
        validate_structure(args[0], _depth=_depth + 1, _budget=_budget)
        return

    if op in _BOOLEAN_OPS:
        args = node.get("args")
        if not isinstance(args, list) or not args:
            raise PolicyError(f"'{op}' needs a nonempty list of arguments.")
        for arg in args:
            validate_structure(arg, _depth=_depth + 1, _budget=_budget)
        return

    if not isinstance(node.get("fact"), str):
        raise PolicyError("A comparison node needs a string 'fact'.")
    if op in _MEMBERSHIP_OPS and not isinstance(node.get("value"), list):
        raise PolicyError(f"'{op}' needs a list 'value'.")


def is_allowed(node, facts):
    """Fail-closed entrypoint for gating a protected action: any malformed
    or unresolvable policy denies rather than raising.
    """
    try:
        return bool(evaluate(node, facts))
    except PolicyError:
        return False


def trace_evaluate(node, facts):
    """Return the same fail-closed result as is_allowed with visited-node evidence."""
    trace = []
    try:
        allowed = bool(evaluate(node, facts, _trace=trace))
    except PolicyError as exc:
        return False, str(exc), trace[0]
    return allowed, None, trace[0]
