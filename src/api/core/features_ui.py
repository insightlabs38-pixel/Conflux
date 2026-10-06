"""Verifier for the `ui_base` property (PD-F003-B02-T01): the base screen of a feature.

A feature an organizer or participant works with has a base screen: one component that loads its
records from the feature's own routes, with a test that renders it. The web source is not part of
the running API, so what the running system can say is the claim itself; the checks that need the
source tree run in CI (`check_static`) and hold the claim to the code:

- `component:<src/web path>` (one or more): the file exists, and the screen talks to the
  feature's API: among the non-test sources of the component's own folder there is a quoted
  string holding the last literal segment of a route the feature claims under `authorization`
  (`tracks/`, `messages/`), so a component cannot be named for a feature it never reads.
- `test:<src/web path>` (one or more): the test file exists and imports one of the components.
- `no_ui@<reason>`: there is no screen yet, and why (a feature configured only through the API or
  another feature's screen). A feature whose screen is owed is `planned` with the owning task.
"""

import re
from pathlib import Path

from . import features
from .features import problem

MIN_REASON = 20
SEGMENT = re.compile(r"<[^>]*>")


def parse(claim):
    components, tests, reasons, other = [], [], {}, []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "component":
            components.append(rest)
        elif kind == "test":
            tests.append(rest)
        elif head == "no_ui":
            reasons["no_ui"] = reason
        else:
            other.append(ref)
    return components, tests, reasons, other


def route_words(feature, system) -> list[str]:
    """The last literal path segment of each route the feature claims (`tracks`, `my-team`)."""
    auth = feature.claims.get("authorization")
    words = []
    if auth is None or auth.state != "provided":
        return words
    for ref in auth.refs:
        if ref.startswith("route:"):
            pattern = system.routes().get(ref.partition(":")[2], "")
            literal = [s for s in SEGMENT.sub("", pattern).split("/") if s]
            if literal:
                words.append(literal[-1])
    return sorted(set(words))


def facts(feature, system) -> dict:
    claim = feature.claims.get("ui_base")
    if claim is None or claim.state != "provided":
        return {}
    components, tests, reasons, _ = parse(claim)
    if "no_ui" in reasons:
        return {"screen": "none yet", "why": reasons["no_ui"]}
    return {
        "screens": [path.rsplit("/", 1)[-1] for path in components],
        "tests": [path.rsplit("/", 1)[-1] for path in tests],
        "reads": route_words(feature, system),
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="ui_base"))

    components, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not component:, test: or no_ui@.")
    if "no_ui" in reasons:
        if components or tests:
            bad("both", "A feature cannot have a screen and say it has none.")
        if len(reasons["no_ui"].strip()) < MIN_REASON:
            bad("no_reason", "Say why there is no screen (a short sentence).")
        return found
    if not components:
        bad("no_component", "Name the base screen (component:<path>) or say why not (no_ui@).")
    if not tests:
        bad("no_test", "Name the test that renders it (test:<path>).")
    for path in components:
        if not re.fullmatch(r"src/web/[\w./-]+\.tsx", path) or ".test." in path:
            bad("component_path", f"'{path}' is not a component under src/web.")
    for path in tests:
        if not re.fullmatch(r"src/web/[\w./-]+\.test\.tsx?", path):
            bad("test_path", f"'{path}' is not a test under src/web.")
    if components and not route_words(feature, system):
        bad("no_routes", "The feature claims no routes under authorization for the screen to read.")
    return found


def _sources(folder: Path):
    return [
        p
        for p in folder.glob("*.ts*")
        if p.is_file() and ".test." not in p.name and p.suffix in (".ts", ".tsx")
    ]


def static(feature, claim, root) -> list[dict]:
    """CI: the screens and tests exist, a test imports a screen, and a screen reads the feature."""
    from .features import System

    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="ui_base"))

    components, tests, _, _ = parse(claim)
    if not components:
        return found
    root = Path(root)
    words = route_words(feature, System())
    folders = set()
    for path in components:
        if not (root / path).is_file():
            bad("component_missing", f"'{path}' does not exist.")
        else:
            folders.add((root / path).parent)
    texts = [p.read_text() for folder in folders for p in _sources(folder)]
    if words and folders and not any(f"{word}/" in text for word in words for text in texts):
        bad(
            "screen_reads_nothing",
            f"No source beside {', '.join(sorted(Path(c).name for c in components))} mentions "
            f"{', '.join(w + '/' for w in words)}; the screen does not read this feature.",
        )
    names = {Path(c).stem for c in components}
    imported = False
    for path in tests:
        file = root / path
        if not file.is_file():
            bad("test_missing", f"'{path}' does not exist.")
            continue
        text = file.read_text()
        imported = imported or any(re.search(rf"\b{re.escape(n)}\b", text) for n in names)
    if tests and not imported:
        bad("test_unrelated", "No named test mentions the screen it should render.")
    return found


features.register_verifier("ui_base", verify, facts=facts, static=static)
