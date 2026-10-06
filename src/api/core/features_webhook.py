"""Verifier for the `webhook` property (PD-F003-B02-T07): which audited changes reach subscribers.

A change is audited with `record_mutation(action=...)`; passing `event_type=...` to the same call
also writes a pending `DomainEvent` in the same transaction (the outbox), and subscribers receive
those events as signed webhooks (`integrations.webhooks`). A feature's audited changes are the
`write:` refs of its `audit` claim, and each of them is either delivered or says why not:

- `emit:<action>=<event type>`: the code records the action with that event type in the same
  `record_mutation` call (a helper that hands its `action` and `event_type` on counts), and the type
  is one a subscription may ask for (`integrations.webhook_views.EVENT_TYPE`);
- `silent:<action>@<reason>`: no call of the code records the action with an event type, and why
  subscribers do not need it;
- `test:<path>::<name>`: the proof, a test that sends each audited change and reads the outbox
  (CI checks it exists).

Every audited change must be exactly one of the two, so a new audited change fails until it is
classified, and an entry for an action the feature does not audit is refused. The report lists the
events a feature emits and what stays silent.
"""

import ast
import re
from functools import lru_cache
from pathlib import Path

from django.apps import apps

from . import features
from .features import AUDIT_ACTION, _assigned_literals, _call_name, problem
from .features_audit import parse as parse_audit

MIN_REASON = 20
EVENT_TYPE = re.compile(r"[a-z][a-z_]*(?:\.[a-z][a-z_]*)+")


def _literals(node, names) -> set[str]:
    """The dotted strings an expression can be: a constant, a conditional's branches, or a name
    assigned some in the same file."""
    if node is None:
        return set()
    values = names.get(node.id, []) if isinstance(node, ast.Name) else [node]
    return {
        part.value
        for value in values
        for part in ast.walk(value)
        if isinstance(part, ast.Constant)
        and isinstance(part.value, str)
        and AUDIT_ACTION.fullmatch(part.value)
    }


def _keyword(call, name):
    return next((kw.value for kw in call.keywords if kw.arg == name), None)


def _helpers(trees) -> dict[str, tuple[str, object]]:
    """Functions that hand their own `action` argument on to `record_mutation`, and what they do
    with the event type: `same` (the action is the event type), `arg:<name>` (a parameter they hand
    on), `fixed:<value>` or `none`."""
    found = {}
    for tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            arguments = {a.arg for a in (*node.args.args, *node.args.kwonlyargs)}
            for call in ast.walk(node):
                if not (isinstance(call, ast.Call) and _call_name(call) == "record_mutation"):
                    continue
                action = _keyword(call, "action")
                if getattr(action, "id", None) not in arguments:
                    continue
                event = _keyword(call, "event_type")
                if event is None:
                    found[node.name] = ("none", None)
                elif getattr(event, "id", None) == action.id:
                    found[node.name] = ("same", None)
                elif getattr(event, "id", None) in arguments:
                    found[node.name] = ("arg", event.id)
                else:
                    found[node.name] = ("fixed", event)
    return found


@lru_cache(maxsize=1)
def scan_outbox() -> dict[str, dict]:
    """Every audit action the code records, with the event types written to the outbox beside it
    (`emits`) and whether some call writes none (`silent`), read from the source."""
    parsed = []
    for config in apps.get_app_configs():
        root = Path(config.path)
        if "site-packages" in root.parts:
            continue
        for file in root.rglob("*.py"):
            if {"migrations", "tests"} & set(file.parts) or file.name.startswith("test_"):
                continue
            try:
                source = file.read_text()
                tree = ast.parse(source)
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            if "record_mutation" in source:
                parsed.append(tree)
    own = {id(tree): _helpers([tree]) for tree in parsed}
    shared: dict[str, set] = {}
    for (
        table
    ) in own.values():  # a helper imported from another file counts when that is unambiguous
        for name, spec in table.items():
            shared.setdefault(name, set()).add(repr(spec))
    elsewhere = {
        name: spec
        for table in own.values()
        for name, spec in table.items()
        if len(shared[name]) == 1
    }
    found: dict[str, dict] = {}
    for tree in parsed:
        helpers = {**elsewhere, **own[id(tree)]}
        names = _assigned_literals(tree)
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            name = _call_name(call)
            if name != "record_mutation" and name not in helpers:
                continue
            action = _keyword(call, "action")
            actions = _literals(action, names)
            if name == "record_mutation":
                event = _keyword(call, "event_type")
                same = event is not None and getattr(event, "id", None) == getattr(action, "id", 0)
                types = actions if same else _literals(event, names)
                none = event is None
            else:
                mode, extra = helpers[name]
                if mode == "same":
                    types, none = actions, False
                elif mode == "arg":
                    given = _keyword(call, extra)
                    types, none = _literals(given, names), given is None
                elif mode == "fixed":
                    types, none = _literals(extra, names), False
                else:
                    types, none = set(), True
            for value in actions:
                row = found.setdefault(value, {"emits": set(), "silent": False})
                row["emits"] |= types
                row["silent"] = row["silent"] or none
    return found


def parse(claim):
    emits, silent, tests, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        if kind == "emit":
            action, _, event_type = rest.partition("=")
            emits.append((action, event_type))
        elif kind == "silent":
            action, _, reason = rest.partition("@")
            silent.append((action, reason))
        elif kind == "test":
            tests.append(rest)
        else:
            other.append(ref)
    return emits, silent, tests, other


def audited(feature) -> list[str]:
    claim = feature.claims.get("audit")
    if claim is None or claim.state != "provided":
        return []
    return sorted({action for _, _, action, _ in parse_audit(claim)[0]})


def facts(feature, system) -> dict:
    claim = feature.claims.get("webhook")
    if claim is None or claim.state != "provided":
        return {}
    emits, silent, _, _ = parse(claim)
    return {
        "emits": [f"{action} → {event_type}" for action, event_type in emits],
        "silent": [action for action, _ in silent],
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="webhook"))

    emits, silent, tests, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not emit:<action>=<type>, silent:<action>@<reason> or test:.")
    if (emits or silent) and not tests:
        bad("no_test", "Name the test that sends each change and reads the outbox (test:).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    scanned = scan_outbox()
    pattern = system.resolve("integrations.webhook_views:EVENT_TYPE") or EVENT_TYPE
    own = set(audited(feature))
    classified: dict[str, int] = {}
    for action, event_type in emits:
        classified[action] = classified.get(action, 0) + 1
        if action not in own:
            bad("action_not_audited", f"'{action}' is not an audited change of this feature.")
            continue
        if not pattern.fullmatch(event_type):
            bad("type_shape", f"'{event_type}' is not an event type a subscription can ask for.")
        elif event_type not in scanned.get(action, {}).get("emits", ()):
            bad(
                "emit_not_recorded", f"The code never records {action} with the event {event_type}."
            )
    for action, reason in silent:
        classified[action] = classified.get(action, 0) + 1
        if action not in own:
            bad("action_not_audited", f"'{action}' is not an audited change of this feature.")
            continue
        if len(reason.strip()) < MIN_REASON:
            bad("no_reason", f"Say why subscribers do not need {action} (a short sentence).")
        if scanned.get(action, {}).get("emits"):
            bad(
                "silent_but_emits", f"{action} is recorded with an event type, so it is not silent."
            )
    for action in sorted(own):
        if classified.get(action, 0) == 0:
            bad("unclassified", f"The audited change {action} is neither emit: nor silent:.")
        elif classified[action] > 1:
            bad("classified_twice", f"The audited change {action} is classified twice.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "webhook")


features.register_verifier("webhook", verify, facts=facts, static=static)
