"""Verifier for the `idempotency` property (PD-F003-B01-T05): what sending a change twice does.

Every change a feature accepts declares how it behaves when the same request arrives again (a
retry after a timeout, a double click, two callers at once), and the declaration is held to the
system:

- `mode:<route>:<METHOD>=natural`: the change sets a state or moves a state machine forward, so
  repeating it leaves the same state (a second delete finds nothing, a second finalize finds the
  version it made). Nothing to resolve; the retry test proves it.
- `=unique@<app.Model>.<constraint>`: a duplicate is refused by a uniqueness constraint the model
  really has.
- `=token@<app.Model>.<field>`: a single-use token (a unique field) is what authorizes the change,
  so the second use is refused.
- `=locked@<app.Model>.<field>` or `=locked@<dotted function>`: callers are serialized, either by
  a version or revision field the model carries (a stale write is refused) or by a function whose
  code takes a row lock (`select_for_update`).
- `=keyed`: the view takes an `Idempotency-Key` (`core.idempotency.IdempotentMixin` is in its
  bases), so a retry with the same key returns the first response and runs once.
- `=none@<reason>`: nothing protects the change and a repeat repeats it; the reason says why that
  is accepted.
- completeness is derived: every writing method of every route the feature claims under
  `authorization` needs a `mode:` ref.
- `test:<path>::<name>`: the proof, which sends each change twice and checks what the second send
  did against the declared mode (a CI check confirms the file and the test exist).
"""

from . import features
from .features import problem

MODES = ("natural", "unique", "token", "locked", "keyed", "none")
WRITES = ("POST", "PUT", "PATCH", "DELETE")
MIN_REASON = 20


def parse(claim):
    """(`route`, `METHOD`, `mode`, `detail`, ref) for each `mode:` ref, and the other refs."""
    modes, other = [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        if kind != "mode":
            other.append(ref)
            continue
        target, _, tail = rest.partition("=")
        route, _, method = target.rpartition(":")
        mode, _, detail = tail.partition("@")
        modes.append((route, method, mode, detail, ref))
    return modes, other


def write_methods(system, route) -> list[str]:
    pattern = system.routes().get(route)
    return sorted(
        {r["method"] for r in system.permission_matrix() if r["path"] == pattern} & set(WRITES)
    )


def _field(system, dotted):
    label, _, name = dotted.rpartition(".")
    model = system.model(label)
    if model is None:
        return None
    try:
        return model._meta.get_field(name)
    except Exception:  # noqa: BLE001 - FieldDoesNotExist and friends
        return None


def _constraint(system, dotted) -> bool:
    from django.db import models

    label, _, name = dotted.rpartition(".")
    model = system.model(label)
    return model is not None and any(
        isinstance(c, models.UniqueConstraint) and c.name == name for c in model._meta.constraints
    )


def _takes_a_lock(system, dotted) -> bool:
    import inspect

    target = system.resolve(dotted) or system.resolve_method(dotted)
    if target is None:
        return False
    try:
        return "select_for_update" in inspect.getsource(target)
    except (OSError, TypeError):
        return False


def _keyed(system, route) -> bool:
    from .idempotency import IdempotentMixin

    view = system.view_class(route)
    return view is not None and issubclass(view, IdempotentMixin)


def facts(feature, system) -> dict:
    claim = feature.claims.get("idempotency")
    if claim is None or claim.state != "provided":
        return {}
    modes, _ = parse(claim)
    return {
        "repeats": [
            f"{method} {route}: {mode}" + (f" ({detail})" if detail else "")
            for route, method, mode, detail, _ in modes
        ],
        "modes": sorted({mode for _, _, mode, _, _ in modes}),
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="idempotency"))

    if system.model(feature.model) is None:
        return found
    modes, other = parse(claim)
    if not any(r.startswith("test:") for r in other):
        bad("no_test", "Name the test that sends each change twice (test:).")
    for ref in other:
        if not ref.startswith("test:"):
            bad("bad_ref", f"'{ref}' is not mode: or test:.")
    if not modes:
        bad(
            "no_modes", "Name how each change behaves when repeated (mode:<route>:<METHOD>=<mode>)."
        )
    seen = set()
    for route, method, mode, detail, ref in modes:
        if not route or method not in WRITES:
            bad("bad_ref", f"'{ref}' is not mode:<route>:<METHOD>=<mode>.")
            continue
        if (route, method) in seen:
            bad("mode_twice", f"{method} {route} is claimed twice.")
        seen.add((route, method))
        if route not in system.routes():
            bad("route_missing", f"There is no route named '{route}'.")
        elif method not in write_methods(system, route):
            bad("method_unknown", f"{route} does not accept {method}.")
        if mode not in MODES:
            bad("mode_unknown", f"'{mode}' is not one of {', '.join(MODES)}.")
        elif mode == "natural" and detail:
            bad("mode_detail", "A natural mode takes no detail.")
        elif mode == "unique" and not _constraint(system, detail):
            bad("unique_missing", f"'{detail}' is not a uniqueness constraint of that model.")
        elif mode == "token":
            field = _field(system, detail)
            if field is None or not getattr(field, "unique", False):
                bad("token_missing", f"'{detail}' is not a unique field.")
        elif (
            mode == "locked"
            and _field(system, detail) is None
            and not _takes_a_lock(system, detail)
        ):
            bad(
                "lock_missing",
                f"'{detail}' is neither a version field nor code that takes a row lock.",
            )
        elif mode == "keyed" and route in system.routes() and not _keyed(system, route):
            bad("not_keyed", f"The view behind {route} does not take an Idempotency-Key.")
        elif mode == "none" and len(detail.strip()) < MIN_REASON:
            bad("no_reason", "Say why a repeated change may repeat (at least a short sentence).")
    auth = feature.claims.get("authorization")
    if auth is not None and auth.state == "provided":
        for ref in auth.refs:
            if not ref.startswith("route:"):
                continue
            route = ref.partition(":")[2]
            for method in write_methods(system, route):
                if (route, method) not in seen:
                    bad("mode_missing", f"{method} {route} changes data and declares no mode.")
    return found


def static(feature, claim, root) -> list[dict]:
    """CI: the proving tests exist. The proof is `tests/integration/test_feature_idempotency.py`,
    which sends every claimed change twice and checks the second send against the mode."""
    return features.static_test_refs(feature, claim, root, "idempotency")


features.register_verifier("idempotency", verify, facts=facts, static=static)
