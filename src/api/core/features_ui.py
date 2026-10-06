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


# --- ui_advanced (PD-F003-B02-T02) --------------------------------------------------------------
#
# Advanced and expert functionality stays behind progressive disclosure and is built from the
# shared advanced components (`src/web/components`: grids, filters, saved views, bulk planner,
# preview bar, version compare, rich editor, schema form, explanations, provenance) rather than
# written again per screen. A `ui_advanced` claim names each use:
#
# - `uses:<Component>@<src/web path>` (one or more): the shared component exists and the named
#   screen file imports it, and that file reads the feature (a quoted last route segment of a
#   claimed route, the key of the feature's query entity, or the feature's own key) so a use
#   cannot be borrowed from another feature's screen;
# - `no_advanced@<reason>`: nothing beyond the base screen, and why. A feature whose advanced screen
#   is owed is `planned` with the owning task.

ADVANCED_COMPONENTS = (
    "ArtifactPreview",
    "BulkPlanner",
    "ConsequenceDialog",
    "DataGrid",
    "DiffView",
    "EntityGrid",
    "ExplanationView",
    "FilterBuilder",
    "NotesDialog",
    "OperationStatus",
    "PreviewBar",
    "ProvenanceView",
    "RichDoc",
    "RichEditor",
    "SchemaForm",
    "ThreadPanel",
    "VersionCompare",
    "ViewBar",
)


def parse_advanced(claim):
    uses, reasons, other = [], {}, []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "uses":
            component, _, path = rest.partition("@")
            uses.append((component, path))
        elif head == "no_advanced":
            reasons["no_advanced"] = reason
        else:
            other.append(ref)
    return uses, reasons, other


def advanced_facts(feature, system) -> dict:
    claim = feature.claims.get("ui_advanced")
    if claim is None or claim.state != "provided":
        return {}
    uses, reasons, _ = parse_advanced(claim)
    if "no_advanced" in reasons:
        return {"advanced": "none beyond the base screen", "why": reasons["no_advanced"]}
    return {"uses": [f"{c} in {p.rsplit('/', 1)[-1]}" for c, p in uses]}


def advanced_verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="ui_advanced"))

    uses, reasons, other = parse_advanced(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not uses:<Component>@<path> or no_advanced@.")
    if "no_advanced" in reasons:
        if uses:
            bad("both", "A feature cannot use advanced components and say it has none.")
        if len(reasons["no_advanced"].strip()) < MIN_REASON:
            bad("no_reason", "Say why nothing goes beyond the base screen (a short sentence).")
        return found
    if not uses:
        bad("no_uses", "Name each shared component the screens use or say why none (no_advanced@).")
    seen = set()
    for component, path in uses:
        if component not in ADVANCED_COMPONENTS:
            bad("component_unknown", f"'{component}' is not a shared advanced component.")
        if not re.fullmatch(r"src/web/features/[\w./-]+\.tsx", path) or ".test." in path:
            bad("screen_path", f"'{path}' is not a screen under src/web/features.")
        if (component, path) in seen:
            bad("use_twice", f"{component} in {path} is claimed twice.")
        seen.add((component, path))
    return found


def feature_words(feature, system) -> list[str]:
    words = [*route_words(feature, system), feature.key]
    search = feature.claims.get("search")
    if search is not None and search.state == "provided":
        words += [r.partition(":")[2] for r in search.refs if r.startswith("entity:")]
    return sorted(set(words))


def advanced_static(feature, claim, root) -> list[dict]:
    """CI: each named screen imports the shared component and reads the feature."""
    from .features import System

    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="ui_advanced"))

    uses, _, _ = parse_advanced(claim)
    root = Path(root)
    words = feature_words(feature, System())
    for component, path in uses:
        if component not in ADVANCED_COMPONENTS:
            continue
        shared = root / "src/web/components" / f"{component}.tsx"
        if not shared.is_file():
            bad("component_missing", f"The shared component {component} does not exist.")
        screen = root / path
        if not screen.is_file():
            bad("screen_missing", f"'{path}' does not exist.")
            continue
        text = screen.read_text()
        if not re.search(rf"from \"[./]*(?:\.\./)*components/{component}\"", text):
            bad("not_imported", f"{Path(path).name} does not import {component}.")
        if words and not any(f"{word}/" in text or f'"{word}"' in text for word in words):
            bad(
                "screen_reads_nothing",
                f"{Path(path).name} mentions none of {', '.join(words)}; it does not read this "
                "feature.",
            )
    return found


features.register_verifier(
    "ui_advanced", advanced_verify, facts=advanced_facts, static=advanced_static
)
