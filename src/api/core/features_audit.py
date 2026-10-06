"""Verifier for the `audit` property (PD-F003-B01-T04): every change a feature accepts is audited.

The platform records a change by writing an `AuditEvent` in the same transaction as the change
(`audit.services.record_mutation`), and the action is a literal `subject.verb` in the code. A
`provided` claim says which action each writing route records, and the verifier holds it to the
system:

- `write:<route>:<METHOD>=<action>`: the route must exist and accept that writing method (the
  permission matrix lists it), and the action must be one the code records (`System.audit_actions`
  reads the `record_mutation` calls from the source) and follow `subject.verb`. The action must be
  recorded by the app that owns the feature's model or the app of the route's view, so a claim
  cannot borrow an unrelated feature's action.
- completeness is derived: when the feature claims its routes under `authorization`, every writing
  method of each of those routes must have a `write:` ref, so a new writing route fails until it is
  audited.
- `test:<path>::<name>`: the proof, a test that sends each change and reads the audit row it left
  (a CI check confirms the file and the test exist).

The report adds the derived list of changes and actions so the page shows what is audited.
"""

from . import features
from .features import AUDIT_ACTION, problem

WRITES = ("POST", "PUT", "PATCH", "DELETE")


def parse(claim):
    """(`route`, `METHOD`, `action`) for each well-formed `write:` ref, and the other refs."""
    writes, other = [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        if kind != "write":
            other.append(ref)
            continue
        target, _, action = rest.partition("=")
        route, _, method = target.rpartition(":")
        writes.append((route, method, action, ref))
    return writes, other


def _rows(system, route):
    pattern = system.routes().get(route)
    return [r for r in system.permission_matrix() if r["path"] == pattern] if pattern else []


def write_methods(system, route) -> list[str]:
    return sorted({r["method"] for r in _rows(system, route) if r["method"] in WRITES})


def facts(feature, system) -> dict:
    claim = feature.claims.get("audit")
    if claim is None or claim.state != "provided":
        return {}
    writes, _ = parse(claim)
    return {
        "changes": [f"{method} {route}: {action}" for route, method, action, _ in writes],
        "actions": sorted({action for _, _, action, _ in writes}),
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="audit"))

    model = system.model(feature.model)
    if model is None:
        return found
    writes, other = parse(claim)
    known = system.audit_actions()
    if not any(r.startswith("test:") for r in other):
        bad("no_test", "Name the test that sends each change and reads its audit row (test:).")
    for ref in other:
        if not ref.startswith("test:"):
            bad("bad_ref", f"'{ref}' is not write: or test:.")
    if not writes:
        bad("no_writes", "Name each change and its audit action (write:<route>:<METHOD>=<action>).")
    seen = set()
    for route, method, action, ref in writes:
        if not route or method not in WRITES or not action:
            bad("bad_ref", f"'{ref}' is not write:<route>:<METHOD>=<action>.")
            continue
        if (route, method) in seen:
            bad("write_twice", f"{method} {route} is claimed twice.")
        seen.add((route, method))
        if route not in system.routes():
            bad("route_missing", f"There is no route named '{route}'.")
        elif method not in write_methods(system, route):
            bad("method_unknown", f"{route} does not accept {method}.")
        if not AUDIT_ACTION.fullmatch(action):
            bad("action_format", f"'{action}' is not of the form subject.verb.")
        elif action not in known:
            bad("action_missing", f"No code records the audit action '{action}'.")
        else:
            homes = set(known[action])
            owners = {model._meta.app_label}
            rows = _rows(system, route)
            owners |= {r["resource"] for r in rows}
            if not homes & owners:
                bad(
                    "action_elsewhere",
                    f"'{action}' is recorded by {', '.join(sorted(homes))}, "
                    f"not by the app of {route} or of the feature's model.",
                )
    auth = feature.claims.get("authorization")
    if auth is not None and auth.state == "provided":
        for ref in auth.refs:
            if not ref.startswith("route:"):
                continue
            route = ref.partition(":")[2]
            for method in write_methods(system, route):
                if (route, method) not in seen:
                    bad(
                        "write_unaudited", f"{method} {route} changes data and has no audit action."
                    )
    return found


def static(feature, claim, root) -> list[dict]:
    """CI: the proving tests exist. The proof itself is `tests/integration/test_feature_audit.py`,
    which sends every claimed change and reads the audit row, so the claim cannot drift from it."""
    return features.static_test_refs(feature, claim, root, "audit")


features.register_verifier("audit", verify, facts=facts, static=static)
