"""Verifier for the `bulk` property (PD-F003-B02-T03): the bulk operations a feature takes part in.

The platform has one bulk planner (`communications.bulk`): an action is registered once, previewed
without writing, applied only with the preview's token, audited and receipted. A feature either has
actions in that registry or says why a batch makes no sense for it, and a claim is held to the
registry:

- `action:<key>=<audit action>` (one or more): the key is a registered planner action, no other
  feature claims it, and the audit action is what the action records for each record it changes:
  one the code records (`System.audit_actions`), written by the app that owns the feature or named
  for it (`project.track_moved` for a project), and, when the handler writes it itself, one of the
  `action=` literals in the handler's own source, so a claim cannot borrow another feature's change.
- `test:<path>::<name>` (one or more): the proof, a test that previews and applies the action (a CI
  check confirms the file and the test exist).
- `no_bulk@<reason>`: a batch does not fit the feature, and why (a single record per event, a
  setting, a record only its owner writes). A feature whose actions are owed is `planned` with the
  owning task.

That every registered action is claimed is checked against the registry by
`tests/integration/test_feature_bulk.py`. The report lists each action's label, the fields it takes
and the audit action it records.
"""

import ast
import inspect
import re
import textwrap

from . import features
from .features import AUDIT_ACTION, problem

MIN_REASON = 20
PLANNER = "communications.bulk:ACTIONS"


def parse(claim):
    actions, tests, reasons, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "action":
            key, _, audit = rest.partition("=")
            actions.append((key, audit))
        elif kind == "test":
            tests.append(rest)
        elif head == "no_bulk":
            reasons.append(reason)
        else:
            other.append(ref)
    return actions, tests, reasons, other


def planner(system) -> dict:
    return system.resolve(PLANNER) or {}


def handler_literals(action) -> set[str]:
    """The `action=` string literals the handler hands to its own calls (none when it delegates)."""
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(action.handler)))
    except (OSError, TypeError, SyntaxError):
        return set()
    return {
        kw.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for kw in node.keywords
        if kw.arg == "action" and isinstance(kw.value, ast.Constant)
    }


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def owns(feature, audit, system) -> bool:
    """The change belongs to the feature: its app records it, or it is named for the feature."""
    app, _, model = feature.model.partition(".")
    subject = audit.partition(".")[0]
    return app in system.audit_actions().get(audit, ()) or subject in {snake(model), feature.key}


def facts(feature, system) -> dict:
    claim = feature.claims.get("bulk")
    if claim is None or claim.state != "provided":
        return {}
    actions, _, reasons, _ = parse(claim)
    if reasons:
        return {"bulk": "not offered", "why": reasons[0]}
    registry = planner(system)
    rows = []
    for key, audit in actions:
        action = registry.get(key)
        if action is None:
            continue
        fields = sorted(action.required) + [f"{name}?" for name in sorted(action.optional)]
        takes = ", ".join(fields) if fields else "a params object"
        rows.append(f"{key} ({action.label}): takes {takes}; records {audit}")
    return {"bulk_actions": rows}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="bulk"))

    actions, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not action:<key>=<audit action>, test: or no_bulk@.")
    if reasons:
        if actions or tests:
            bad("both", "A feature cannot have bulk actions and say a batch does not fit it.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why a batch does not fit (a short sentence).")
        return found
    if not actions:
        bad("no_action", "Name each planner action (action:<key>=<audit action>) or no_bulk@.")
    if actions and not tests:
        bad("no_test", "Name the test that previews and applies the action (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    registry = planner(system)
    if actions and not registry:
        bad("planner_missing", f"The bulk planner registry '{PLANNER}' cannot be read.")
        return found
    seen = set()
    audited = system.audit_actions()
    for key, audit in actions:
        action = registry.get(key)
        if action is None:
            bad("action_unknown", f"'{key}' is not a registered bulk action.")
        if key in seen:
            bad("action_twice", f"'{key}' is claimed twice.")
        seen.add(key)
        if not AUDIT_ACTION.fullmatch(audit):
            bad("audit_shape", f"'{audit}' is not a subject.verb audit action.")
        elif audit not in audited:
            bad("audit_unknown", f"The code never records '{audit}' (action '{key}').")
        elif not owns(feature, audit, system):
            bad("audit_foreign", f"'{audit}' is neither written by this app nor named for it.")
        if action is not None:
            literals = handler_literals(action)
            if literals and audit not in literals:
                bad(
                    "audit_not_written",
                    f"The handler of '{key}' writes {', '.join(sorted(literals))}, not '{audit}'.",
                )
        for other_feature in features.FEATURES.values():
            if other_feature.key == feature.key:
                continue
            other_claim = other_feature.claims.get("bulk")
            if other_claim is not None and other_claim.state == "provided":
                if key in {k for k, _ in parse(other_claim)[0]}:
                    bad("action_shared", f"'{key}' is also claimed by '{other_feature.key}'.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "bulk")


features.register_verifier("bulk", verify, facts=facts, static=static)
