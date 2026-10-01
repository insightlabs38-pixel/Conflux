"""Why a decision came out the way it did, in one shape (POLICY_EXPLAIN, PD-F002-B02-T06).

The platform already explains itself three ways: a policy evaluation returns a visited-node trace,
event readiness returns checklist items, and a delete or status preview returns blockers and
consequences. This module gives all three one **Explanation** the browser draws the same way, and
is where a feature's next "why was this refused" goes:

    {"outcome": "allowed" | "blocked" | "needs_action" | "unknown",
     "summary": "One sentence.",
     "reasons": [{"code", "severity": "info" | "warning" | "blocker", "message",
                  "facts": {...}?, "fix": {"destination", "section"}?}],
     "total": 3, "truncated": false}

Rules
- **It explains a decision the domain already made; it never decides.** Nothing here computes a
  score, a permission, a deadline or a policy outcome, and an adapter only reads the payload the
  domain produced. The existing endpoints keep their shapes; the explanation is added beside them.
- Derived on every read and never stored. Pure and deterministic: the same payload gives the same
  words in the same order.
- **Facts respect the reader.** An adapter takes `detailed`: when it is false no fact values appear
  anywhere in the explanation, only the sentence the domain already chose to show that person.
- Bounded: at most 50 reasons (`total` counts them all), messages 500 characters, 10 facts a
  reason, fact text 200 characters. Every string is data for a text node.
"""

import json

OUTCOMES = ("allowed", "blocked", "needs_action", "unknown")
SEVERITIES = ("info", "warning", "blocker")
MAX_REASONS = 50
MAX_MESSAGE = 500
MAX_FACTS = 10
MAX_FACT_TEXT = 200


def _text(value, limit=MAX_MESSAGE) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = "".join(ch if ch.isprintable() else "�" for ch in text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _scalar(value):
    if value is None or isinstance(value, bool | int | float):
        return value
    return _text(value, MAX_FACT_TEXT)


def reason(code, message, *, severity="info", facts=None, fix=None) -> dict:
    """One reason. `facts` are short scalar values behind the message; `fix` points at where it
    is resolved (`{"destination", "section"}`)."""
    if severity not in SEVERITIES:
        raise ValueError(f"Unknown severity '{severity}'.")
    row = {"code": _text(code, 80), "severity": severity, "message": _text(message)}
    if facts:
        row["facts"] = {_text(k, 60): _scalar(v) for k, v in list(facts.items())[:MAX_FACTS]}
    if fix:
        row["fix"] = {
            "destination": _text(fix.get("destination", ""), 60),
            "section": _text(fix["section"], 60) if fix.get("section") else None,
        }
    return row


def explanation(outcome, summary, reasons=()) -> dict:
    if outcome not in OUTCOMES:
        raise ValueError(f"Unknown outcome '{outcome}'.")
    reasons = list(reasons)
    return {
        "outcome": outcome,
        "summary": _text(summary),
        "reasons": reasons[:MAX_REASONS],
        "total": len(reasons),
        "truncated": len(reasons) > MAX_REASONS,
    }


def unknown(summary) -> dict:
    """Nothing was decided (yet): say so rather than imply either answer."""
    return explanation("unknown", summary)


# --- policy evaluation --------------------------------------------------------------------

_MUST = {
    "eq": "equal",
    "ne": "not equal",
    "gt": "be greater than",
    "gte": "be at least",
    "lt": "be less than",
    "lte": "be at most",
    "in": "be one of",
    "not_in": "not be one of",
}
_COMPARISONS = set(_MUST)
_INVERSE = {
    "eq": "ne", "ne": "eq", "gt": "lte", "lte": "gt", "gte": "lt", "lt": "gte",
    "in": "not_in", "not_in": "in",
}  # fmt: skip


def _leaves(node, want, negated=False):
    """The leaf checks that explain why `node` evaluated to `want`, as `(leaf, negated)` pairs.

    An `and` that failed is explained by the children that failed (the rest were never reached), an
    `or` that failed by all of them, a `not` by its child with the answer turned around.
    """
    status = node.get("status")
    children = node.get("children") or []
    if status == "skipped":
        return []
    if status == "error" or node.get("op") in _COMPARISONS | {"true", "false"}:
        return [(node, negated)]
    if node.get("op") == "not":
        return [pair for child in children for pair in _leaves(child, not want, not negated)]
    if node.get("op") in ("and", "or"):
        every = (node["op"] == "and") == want  # all children had to hold
        picked = [
            c
            for c in children
            if c.get("status") != "skipped" and (every or c.get("result") == want)
        ]
        return [pair for child in picked for pair in _leaves(child, want, negated)]
    return [(node, negated)]


def _fact_name(fact):
    return fact.split(":", 1)[1] if ":" in str(fact) else str(fact)


def _leaf_reason(leaf, negated, satisfied, detailed):
    op = leaf.get("op")
    if leaf.get("status") == "error":
        return reason(
            "policy_error",
            f"The policy could not be evaluated: {leaf.get('error', 'unknown problem')}",
            severity="blocker",
        )
    if op in ("true", "false"):  # a fixed check explains the decision it is part of
        return reason(
            "policy_true" if satisfied else "policy_false",
            "The policy always allows this." if satisfied else "The policy always denies this.",
            severity="info" if satisfied else "blocker",
        )
    fact, actual, expected = leaf.get("fact"), leaf.get("actual"), leaf.get("expected")
    facts = {"fact": fact, "actual": actual, "expected": expected} if detailed else None
    if str(fact).startswith("gate_open:"):
        name = _fact_name(fact)
        open_now = bool(actual)
        message = f"The {name} window is {'open' if open_now else 'not open'}."
        return reason(
            "gate_open" if open_now else "gate_closed",
            message,
            severity="info" if satisfied else "blocker",
            facts=facts,
        )
    # Under a `not` the requirement is the opposite of the check as written.
    must = _MUST.get(_INVERSE[op] if negated and op in _INVERSE else op, op)
    if satisfied:
        message = f"{fact} is {actual!r}; it must {must} {expected!r}."
    else:
        message = f"{fact} is {actual!r}, but it must {must} {expected!r}."
    return reason(f"fact:{fact}", message, severity="info" if satisfied else "blocker", facts=facts)


def from_policy_debug(payload: dict, *, detailed: bool = True) -> dict:
    """The explanation of a policy debug result (`policies.debugger.debug_action`).

    `detailed` is for people allowed to read the policy and the facts it checked (organizers); for
    anyone else only the domain's own sentence is returned and no fact values appear.
    """
    sentence = payload.get("reason") or ""
    policy = payload.get("policy")
    if policy is None:
        return explanation(
            "allowed",
            "No policy gates this action.",
            [reason("no_policy", "No policy is attached to this action, so it is not gated.")],
        )
    name = policy.get("name", "the policy")
    trace = payload.get("trace")
    allowed = bool(payload.get("allowed"))
    by_policy = payload.get("policy_allowed")
    rows = []
    if payload.get("exception_grant_reason") is not None and not by_policy:
        rows.append(
            reason(
                "exception_grant",
                f"An exception grant allows it ({payload['exception_grant_reason']}).",
            )
        )
    if payload.get("error"):  # fail-closed: only a grant can still allow it
        rows.append(
            reason(
                "policy_error",
                f"The policy could not be evaluated: {payload['error']}"
                if detailed
                else "The policy could not be evaluated.",
                severity="info" if allowed else "blocker",
            )
        )
        summary = (
            "Allowed by an exception grant although the policy could not be evaluated."
            if allowed
            else "Denied: the policy could not be evaluated."
        )
        return explanation("allowed" if allowed else "blocked", summary, rows)
    if not detailed:
        if not rows:
            rows.append(
                reason(
                    "policy_allowed" if allowed else "policy_denied",
                    sentence or ("Allowed by policy." if allowed else "Denied by policy."),
                    severity="info" if allowed else "blocker",
                )
            )
        return explanation(
            "allowed" if allowed else "blocked",
            sentence or f"Allowed by policy {name!r}.",
            rows,
        )
    if trace:
        satisfied = bool(by_policy)
        for leaf, negated in _leaves(trace, satisfied):
            rows.append(_leaf_reason(leaf, negated, satisfied, True))
        if not satisfied and allowed:  # a grant overrides: the unmet checks are context only
            rows = [rows[0]] + [{**r, "severity": "info"} for r in rows[1:]]
    if allowed:
        summary = (
            f"Allowed by an exception grant although policy {name!r} would deny it."
            if payload.get("exception_grant_reason") is not None and not by_policy
            else f"Allowed by policy {name!r}."
        )
    else:
        summary = sentence or f"Denied by policy {name!r}."
    return explanation("allowed" if allowed else "blocked", summary, rows)


# --- event readiness ----------------------------------------------------------------------


def from_readiness(readiness: dict) -> dict:
    """The explanation of `eventconfig.readiness.compute_readiness`: what is still open."""
    items = readiness.get("items", [])
    open_items = [i for i in items if not i.get("passed")]
    blockers = [i for i in open_items if i.get("severity") == "blocker"]
    warnings = [i for i in open_items if i.get("severity") != "blocker"]
    rows = [
        reason(
            item["id"],
            item.get("detail", ""),
            severity="blocker" if item.get("severity") == "blocker" else "warning",
            facts={"module": item["module"]} if item.get("module", "core") != "core" else None,
            fix=item.get("fix"),
        )
        for item in blockers + warnings
    ]
    if blockers:
        outcome = "blocked"
        summary = f"{len(blockers)} blocker{'s' if len(blockers) != 1 else ''} to resolve" + (
            f" and {len(warnings)} warning{'s' if len(warnings) != 1 else ''}." if warnings else "."
        )
    elif warnings:
        outcome = "needs_action"
        summary = f"{len(warnings)} warning{'s' if len(warnings) != 1 else ''} to look at."
    else:
        outcome, summary = "allowed", "Nothing is unresolved."
    return explanation(outcome, summary, rows)


# --- deletion and status previews ---------------------------------------------------------


def from_consequences(shown: dict) -> dict:
    """The explanation of `eventconfig.consequences.preview`: why it is refused, or what it does."""
    blockers = shown.get("blockers") or []
    rows = [reason(b["code"], b["message"], severity="blocker", facts=_count(b)) for b in blockers]
    rows += [
        reason(c["code"], c["message"], facts=_count(c)) for c in shown.get("consequences") or []
    ]
    if blockers:
        return explanation("blocked", "This cannot be done right now.", rows)
    if shown.get("reversible") is False:
        rows.append(reason("irreversible", "This cannot be undone.", severity="warning"))
    return explanation(
        "allowed",
        "This will have the effects below." if rows else "Nothing else depends on it.",
        rows,
    )


def _count(item):
    return {"count": item["count"]} if item.get("count") is not None else None
