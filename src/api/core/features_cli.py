"""Verifier for the `cli` property (PD-F003-B02-T04): the commands that administer a feature.

The CLI (`conflux-admin`, `sdks/python/conflux_sdk/cli.py`) is a thin client of the generated Python
SDK: its one table `COMMANDS` maps each command to the generated operation(s) it calls, so it holds
no rule of its own and every request still passes the API's authorization, validation and audit. A
feature either has commands in that table or says why a terminal is not the place for it, and a
claim is held to the table:

- `command:<name>` (one or more, `events list`): the command is in the table, every operation it
  calls is in the generated Python client, and every one of them is an operation of the feature's
  own routes (the ones it claims under `authorization`); the claimed commands equal the derived
  set, so a command added for a feature without claiming it fails, and so does a claim of a
  command the CLI does not have.
- `test:<path>::<name>`: the proof, a test that runs the commands through the CLI against the API
  (CI checks it exists).
- `no_cli@<reason>`: the CLI has no command for the feature, and why; a feature whose commands are
  owed is `planned` with the owning task.

The web source and the SDK are not part of the running API, so the report shows the claim and the
table checks run in CI (`check_static`). `tests/integration/test_feature_cli.py` proves that each
claimed command sends the request its operation describes, and that every command in the table is
claimed by a feature or named in `OUTSIDE`.
"""

import importlib
import importlib.util
import re
import sys
from pathlib import Path

from . import features
from .features import problem

MIN_REASON = 20
COMMAND = re.compile(r"[a-z]+(?: [a-z]+)*")

# Commands that belong to no feature of the registry, and why. A command in the table must be
# claimed by a feature or be here, so a new command cannot appear unowned.
OUTSIDE = {
    "whoami": "reads the caller's own identity, which is not a feature of an event",
    "events export": "runs through the archive routes that no feature claims yet (PD-F003-B02-T08)",
    "events import": "runs through the archive routes that no feature claims yet (PD-F003-B02-T08)",
}


def parse(claim):
    commands, tests, reasons, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "command":
            commands.append(rest)
        elif kind == "test":
            tests.append(rest)
        elif head == "no_cli":
            reasons.append(reason)
        else:
            other.append(ref)
    return commands, tests, reasons, other


def facts(feature, system) -> dict:
    claim = feature.claims.get("cli")
    if claim is None or claim.state != "provided":
        return {}
    commands, _, reasons, _ = parse(claim)
    if reasons:
        return {"cli": "no command", "why": reasons[0]}
    return {"commands": [f"conflux-admin {c}" for c in commands]}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="cli"))

    commands, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not command:<name>, test: or no_cli@.")
    if reasons:
        if commands or tests:
            bad("both", "A feature cannot have CLI commands and say it has none.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why the CLI has nothing for this feature (a sentence).")
        return found
    if not commands:
        bad("no_command", "Name each CLI command (command:<name>) or say why none (no_cli@).")
    if commands and not tests:
        bad("no_test", "Name the test that runs the commands (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    seen = set()
    for command in commands:
        if not COMMAND.fullmatch(command):
            bad("command_shape", f"'{command}' is not a command name (lowercase words).")
        if command in seen:
            bad("command_twice", f"'{command}' is claimed twice.")
        seen.add(command)
        for other_feature in features.FEATURES.values():
            other_claim = other_feature.claims.get("cli")
            if (
                other_feature.key != feature.key
                and other_claim is not None
                and other_claim.state == "provided"
                and command in parse(other_claim)[0]
            ):
                bad("command_shared", f"'{command}' is also claimed by '{other_feature.key}'.")
    return found


def load(root):
    """The CLI's command table and the generated operations, read from the source tree."""
    package = Path(root) / "sdks/python/conflux_sdk"
    name = f"_conflux_cli_{abs(hash(str(package)))}"
    spec = importlib.util.spec_from_file_location(
        name, package / "__init__.py", submodule_search_locations=[str(package)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        cli = importlib.import_module(f"{name}.cli")
        generated = importlib.import_module(f"{name}.generated")
        return dict(cli.COMMANDS), dict(generated.OPERATIONS)
    finally:
        for key in [k for k in sys.modules if k == name or k.startswith(name + ".")]:
            del sys.modules[key]


def own_operations(feature, system) -> set[str]:
    from .features_sdk import operations

    return {op["operationId"] for _, _, op in operations(feature, system) if op}


def static(feature, claim, root) -> list[dict]:
    """CI: the table holds the claimed commands, each reaching an operation of the feature."""
    from .features import System

    found = features.static_test_refs(feature, claim, root, "cli")

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="cli"))

    try:
        table, generated = load(root)
    except (OSError, ImportError, AttributeError, SyntaxError) as exc:
        bad("table_unreadable", f"The CLI command table cannot be read ({exc}).")
        return found
    commands, _, _, _ = parse(claim)
    own = own_operations(feature, System())
    for command in commands:
        if command not in table:
            bad("command_missing", f"The CLI has no command '{command}'.")
            continue
        for operation in table[command]:
            if operation not in generated:
                bad("op_not_generated", f"'{command}' calls {operation}, not in the Python client.")
            elif operation not in own:
                bad("command_foreign", f"'{command}' calls {operation}, not one of this feature's.")
    derived = {c for c, ops in table.items() if set(ops) & own}
    for command in sorted(derived - set(commands)):
        if commands:
            bad("command_unclaimed", f"The CLI has '{command}' for this feature; claim it.")
        else:
            bad("cli_exists", f"The claim says no CLI, but the CLI has '{command}' for it.")
    return found


features.register_verifier("cli", verify, facts=facts, static=static)
