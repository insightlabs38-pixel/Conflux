"""The cross-surface completeness contract as code (PD-F003-B01, spec 003).

A deep feature has more than a model and an endpoint: a stable identity and a clear lifecycle,
validation, authorization, audit, idempotency, a REST and SDK representation, search, UI, bulk,
CLI, MCP, Event-as-Code, webhooks, archive, analytics, privacy, extension hooks, versioning and
fixtures (the 21 `PROPERTIES`). This module states which feature provides which, and checks the
claims against the live system, so completeness is written once, derived where it can be and never
hand-copied:

    features.register_feature(features.Feature(
        key="event", label="Event", model="events.Event",
        claims={"identity": features.provided("field:public_id", "route:event-detail")},
        lifecycle=features.Lifecycle("choice", field="status", initial=("draft",),
                                     transitions="events.views:STATUS_FLOW")))

Rules
- A claim is `provided` (with refs that a verifier resolves), `not_applicable` (with a reason) or
  `planned` (with the task that owns it). A property is **landed** once a verifier is registered
  for it; a landed property must be claimed by every registered feature, a `provided` claim needs
  a verifier, and every ref must resolve. A property that has not landed may be left unclaimed.
- Facts are derived from the system (model fields and choices, routes, ...); only the claim, its
  refs, reasons and the lifecycle graph the code does not already hold are declared.
- Advisory at runtime: the report never gates a request. CI (tests) enforces it.
- Read-only: verifiers never write, and `core` imports no domain app; models are reached by label.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field as dc_field
from importlib import import_module

from django.apps import apps
from django.urls import get_resolver

STATES = ("provided", "not_applicable", "planned")
MAX_REASON = 300


@dataclass(frozen=True)
class Property:
    key: str
    label: str
    batch: str  # the batch that owns its verifier


PROPERTIES: dict[str, Property] = {
    p.key: p
    for p in (
        Property("identity", "Identity and lifecycle", "PD-F003-B01"),
        Property("validation", "Validation and invariants", "PD-F003-B01"),
        Property("authorization", "Authorization and scope", "PD-F003-B01"),
        Property("audit", "Audit events", "PD-F003-B01"),
        Property("idempotency", "Idempotency and concurrency", "PD-F003-B01"),
        Property("rest", "REST representation", "PD-F003-B01"),
        Property("sdk", "Generated SDK", "PD-F003-B01"),
        Property("search", "Search and filter fields", "PD-F003-B01"),
        Property("ui_base", "Base UI", "PD-F003-B02"),
        Property("ui_advanced", "Advanced UI", "PD-F003-B02"),
        Property("bulk", "Bulk operations", "PD-F003-B02"),
        Property("cli", "CLI", "PD-F003-B02"),
        Property("mcp", "MCP", "PD-F003-B02"),
        Property("event_as_code", "Event-as-Code", "PD-F003-B02"),
        Property("webhook", "Webhooks and outbox", "PD-F003-B02"),
        Property("archive", "Archive and import", "PD-F003-B02"),
        Property("analytics", "Analytics dimensions", "PD-F003-B03"),
        Property("privacy", "Retention and privacy", "PD-F003-B03"),
        Property("extension", "Extension hooks", "PD-F003-B03"),
        Property("versioning", "Version and migration", "PD-F003-B03"),
        Property("fixtures", "Test fixtures and scenarios", "PD-F003-B03"),
    )
}


@dataclass(frozen=True)
class Claim:
    state: str
    refs: tuple[str, ...] = ()
    reason: str = ""
    owner: str = ""  # for `planned`: the task that will provide it


def provided(*refs: str) -> Claim:
    return Claim("provided", refs=tuple(refs))


def not_applicable(reason: str) -> Claim:
    return Claim("not_applicable", reason=reason)


def planned(owner: str, reason: str = "") -> Claim:
    return Claim("planned", owner=owner, reason=reason)


@dataclass(frozen=True)
class Lifecycle:
    """How a feature's records change state. `choice` reads the states from the model field's
    own choices, `timestamp` and `flag` from a nullable time or a boolean (`states` names the two
    derived states, unset or false first), `none` says why there is no state machine.

    `transitions` is the graph `{from: (to, ...)}`, or `"module:NAME"` pointing at a table the code
    already owns (so it is read, not copied). `via` names what performs the transitions."""

    kind: str
    field: str = ""
    initial: tuple[str, ...] = ()
    transitions: object = dc_field(default_factory=dict)
    terminal: tuple[str, ...] = ()
    via: tuple[str, ...] = ()
    states: tuple[tuple[str, str], ...] = ()
    note: str = ""


@dataclass(frozen=True)
class Feature:
    key: str
    label: str
    model: str  # "app_label.ModelName"
    claims: dict[str, Claim] = dc_field(default_factory=dict)
    lifecycle: Lifecycle | None = None
    id_field: str = "public_id"


FEATURES: dict[str, Feature] = {}
VERIFIERS: dict[str, Callable] = {}
FACTS: dict[str, Callable] = {}  # property -> facts(feature, system) -> dict, derived and shown
STATIC_CHECKS: dict[str, Callable] = {}  # property -> check(feature, claim, root) -> [problem]


def register_feature(feature: Feature) -> None:
    if feature.key in FEATURES and FEATURES[feature.key] != feature:
        raise ValueError(f"Feature '{feature.key}' is already registered.")
    FEATURES[feature.key] = feature


def register_verifier(
    prop: str, verifier: Callable, *, facts: Callable | None = None, static: Callable | None = None
) -> None:
    """`verifier(feature, claim, system)` runs with the report. `facts(feature, system)` adds
    derived facts to the report. `static(feature, claim, root)` checks refs that only the source
    tree can answer (a test file and name) and runs in CI, not in the deployed app."""
    if prop not in PROPERTIES:
        raise ValueError(f"Unknown property '{prop}'.")
    if prop in VERIFIERS and VERIFIERS[prop] is not verifier:
        raise ValueError(f"Property '{prop}' already has a verifier.")
    VERIFIERS[prop] = verifier
    if facts:
        FACTS[prop] = facts
    if static:
        STATIC_CHECKS[prop] = static


def landed() -> list[str]:
    return [key for key in PROPERTIES if key in VERIFIERS]


def problem(code, message, *, feature=None, prop=None) -> dict:
    return {"code": code, "feature": feature, "property": prop, "message": message}


# --- the read-only view of the live system that verifiers use ------------------------------------

_CONVERTER = re.compile(r"<(\w+):(\w+)>")


class System:
    """Facts about the running system, computed on first use and never written."""

    def __init__(self):
        self._routes = None

    def model(self, label: str):
        try:
            return apps.get_model(label)
        except (LookupError, ValueError):
            return None

    def routes(self) -> dict[str, str]:
        """URL name -> pattern, for every named route."""
        if self._routes is None:
            found = {}

            def walk(resolver, prefix=""):
                for pattern in resolver.url_patterns:
                    if hasattr(pattern, "url_patterns"):
                        walk(pattern, prefix + str(pattern.pattern))
                    elif pattern.name:
                        found[pattern.name] = prefix + str(pattern.pattern)

            walk(get_resolver())
            self._routes = found
        return self._routes

    def converters(self, route_name: str) -> list[tuple[str, str]]:
        return _CONVERTER.findall(self.routes().get(route_name, ""))

    def resolve(self, dotted: str):
        """`module:NAME` or `module.path.Name` to the object, or None."""
        try:
            if ":" in dotted:
                module, _, name = dotted.partition(":")
                return getattr(import_module(module), name)
            module, _, name = dotted.rpartition(".")
            return getattr(import_module(module), name)
        except (ImportError, AttributeError, ValueError):
            return None

    def resolve_method(self, dotted: str):
        """`pkg.module.Class.method` to the attribute of the class, or None."""
        owner, _, name = dotted.rpartition(".")
        cls = self.resolve(owner)
        return getattr(cls, name, None) if cls is not None else None


# --- checking ---------------------------------------------------------------------------------


def _claim_problems(feature: Feature, prop: str, claim: Claim) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop=prop))

    if claim.state not in STATES:
        bad("bad_state", f"State '{claim.state}' is not one of {', '.join(STATES)}.")
        return found
    if claim.state == "provided" and not claim.refs:
        bad("no_refs", "A provided claim names how it is provided.")
    if claim.state == "not_applicable" and not claim.reason:
        bad("no_reason", "A claim that does not apply says why.")
    if claim.state == "planned" and not claim.owner:
        bad("no_owner", "A planned claim names the task that owns it.")
    if len(claim.reason) > MAX_REASON:
        bad("reason_too_long", f"A reason is at most {MAX_REASON} characters.")
    if claim.state == "provided" and prop not in VERIFIERS:
        bad(
            "no_verifier", "Nothing can verify this property yet, so it cannot be claimed provided."
        )
    return found


def check(system: System | None = None) -> list[dict]:
    """Every way the claims and the live system disagree, in a stable order."""
    system = system or System()
    found = []
    for feature in sorted(FEATURES.values(), key=lambda f: f.key):
        if system.model(feature.model) is None:
            found.append(
                problem(
                    "model_missing", f"Model '{feature.model}' does not exist.", feature=feature.key
                )
            )
        for prop in feature.claims:
            if prop not in PROPERTIES:
                found.append(
                    problem("unknown_property", f"'{prop}' is not a property.", feature=feature.key)
                )
        for prop in landed():
            claim = feature.claims.get(prop)
            if claim is None:
                found.append(
                    problem(
                        "unclaimed",
                        "A landed property must be claimed.",
                        feature=feature.key,
                        prop=prop,
                    )
                )
                continue
            found += _claim_problems(feature, prop, claim)
            if claim.state == "provided":
                found += VERIFIERS[prop](feature, claim, system)
        for prop, claim in feature.claims.items():
            if prop in PROPERTIES and prop not in landed():
                found += _claim_problems(feature, prop, claim)
    return found


def check_static(root, system: System | None = None) -> list[dict]:
    """The checks that need the source tree (CI). `root` is the repository root."""
    system = system or System()
    found = []
    for feature in sorted(FEATURES.values(), key=lambda f: f.key):
        for prop, check_fn in STATIC_CHECKS.items():
            claim = feature.claims.get(prop)
            if claim is not None and claim.state == "provided":
                found += check_fn(feature, claim, root)
    return found


def derived(feature: Feature, system: System) -> dict:
    """What the system itself says about a feature (nothing here is declared)."""
    model = system.model(feature.model)
    if model is None:
        return {"id_field": feature.id_field, "id_type": None, "states": []}
    out = {"id_field": feature.id_field, "id_type": None, "states": []}
    try:
        out["id_type"] = type(model._meta.get_field(feature.id_field)).__name__
    except Exception:  # noqa: BLE001 - a missing field is reported by the verifier
        pass
    life = feature.lifecycle
    if life and life.kind == "choice" and life.field:
        try:
            choices = model._meta.get_field(life.field).choices or []
            out["states"] = [{"value": str(v), "label": str(label)} for v, label in choices]
        except Exception:  # noqa: BLE001
            pass
    elif life and life.kind in ("timestamp", "flag"):
        out["states"] = [{"value": v, "label": label} for v, label in life.states]
    return out


def transition_graph(life: Lifecycle, system: System) -> dict[str, tuple[str, ...]]:
    table = life.transitions
    if isinstance(table, str):
        table = system.resolve(table) or {}
    return {
        str(source): tuple(targets) if isinstance(targets, (tuple, list, set)) else (str(targets),)
        for source, targets in dict(table).items()
    }


def report(system: System | None = None) -> dict:
    """The matrix the Operations page shows: features by property, derived facts and findings."""
    system = system or System()
    findings = check(system)
    by_feature: dict[str, list[dict]] = {}
    for item in findings:
        by_feature.setdefault(item["feature"] or "", []).append(item)
    rows = []
    for feature in sorted(FEATURES.values(), key=lambda f: f.label):
        life = feature.lifecycle
        rows.append(
            {
                "key": feature.key,
                "label": feature.label,
                "model": feature.model,
                **derived(feature, system),
                "lifecycle": None
                if life is None
                else {
                    "kind": life.kind,
                    "field": life.field,
                    "initial": list(life.initial),
                    "terminal": list(life.terminal),
                    "via": list(life.via),
                    "note": life.note,
                    "transitions": {k: list(v) for k, v in transition_graph(life, system).items()},
                },
                "facts": {
                    prop: fn(feature, system)
                    for prop, fn in FACTS.items()
                    if feature.claims.get(prop) is not None
                },
                "claims": {
                    prop: {
                        "state": claim.state,
                        "refs": list(claim.refs),
                        "reason": claim.reason,
                        "owner": claim.owner,
                    }
                    for prop, claim in feature.claims.items()
                },
                "problems": by_feature.get(feature.key, []),
            }
        )
    totals = {}
    for prop in PROPERTIES:
        counts = {state: 0 for state in STATES}
        counts["unclaimed"] = 0
        for feature in FEATURES.values():
            claim = feature.claims.get(prop)
            counts[claim.state if claim else "unclaimed"] += 1
        totals[prop] = counts
    return {
        "properties": [
            {"key": p.key, "label": p.label, "batch": p.batch, "landed": p.key in VERIFIERS}
            for p in PROPERTIES.values()
        ],
        "features": rows,
        "totals": totals,
        "problems": findings,
        "ok": not findings,
    }
