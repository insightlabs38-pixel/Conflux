"""Verifier for the `event_as_code` property (PD-F003-B02-T06): a feature's place in the document.

Event-as-Code (`integrations.eventascode`) describes an event's configuration as a document that
is exported, validated, planned and applied by name. Configuration belongs in it; runtime
participant data (registrations, projects, submissions, messages) never does. A feature either is a
section of the document or says why it is not, and a claim is held to the module:

- `section:<name>` (one or more): the section is one the module declares (`SECTION_MODELS`, and
  `SECTIONS` plus the `event` fields), and the model that owns the section is the feature's own
  model, so a section cannot be borrowed from another feature; the claimed sections equal the
  derived set (every section the feature's model owns), so a section added for a feature without a
  claim fails.
- `test:<path>::<name>`: the proof, a test that applies the document to an empty event and gets the
  same configuration back (CI checks it exists).
- `no_eac@<reason>`: the feature is not configuration, and why; a feature whose section is owed is
  `planned` with the owning task.

A section owned by no feature of the registry is in `OUTSIDE`, so a new section cannot appear
unowned (`tests/integration/test_feature_eac.py`, which also proves each section writes exactly the
rows it declares). The report lists each section with the records it stands for.
"""

import re

from . import features
from .features import problem

MIN_REASON = 20
MODULE = "integrations.eventascode"

# Sections owned by a model that no feature of the registry covers yet.
OUTSIDE = {
    "base_prizes": "base prizes (events.BasePrize) are not a feature of the registry yet",
    "page": "the event page (presentation.Page) is not a feature of the registry yet",
}


def parse(claim):
    sections, tests, reasons, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "section":
            sections.append(rest)
        elif kind == "test":
            tests.append(rest)
        elif head == "no_eac":
            reasons.append(reason)
        else:
            other.append(ref)
    return sections, tests, reasons, other


def declared(system) -> dict:
    return dict(system.resolve(f"{MODULE}:SECTION_MODELS") or {})


def derived(feature, system) -> list[str]:
    """Every section named for the feature's own model."""
    return sorted(n for n, (owner, _) in declared(system).items() if owner == feature.model)


def facts(feature, system) -> dict:
    claim = feature.claims.get("event_as_code")
    if claim is None or claim.state != "provided":
        return {}
    sections, _, reasons, _ = parse(claim)
    if reasons:
        return {"eac": "not in the document", "why": reasons[0]}
    table = declared(system)
    return {"sections": [f"{n}: {', '.join(table[n][1])}" for n in sections if n in table]}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="event_as_code"))

    sections, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not section:<name>, test: or no_eac@.")
    table = declared(system)
    owned = derived(feature, system)
    if reasons:
        if sections or tests:
            bad("both", "A feature cannot be a section and say it is not configuration.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why it is not configuration (a short sentence).")
        for name in owned:
            bad("eac_exists", f"The document has the section '{name}' for this feature; claim it.")
        return found
    if not sections:
        bad("no_section", "Name each document section (section:<name>) or say why none (no_eac@).")
    if sections and not tests:
        bad("no_test", "Name the test that applies the document (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    if sections and not table:
        bad("module_missing", f"The Event-as-Code module '{MODULE}' cannot be read.")
        return found
    seen = set()
    for name in sections:
        if name in seen:
            bad("section_twice", f"'{name}' is claimed twice.")
        seen.add(name)
        for other_feature in features.FEATURES.values():
            other_claim = other_feature.claims.get("event_as_code")
            if (
                other_feature.key != feature.key
                and other_claim is not None
                and other_claim.state == "provided"
                and name in parse(other_claim)[0]
            ):
                bad("section_shared", f"'{name}' is also claimed by '{other_feature.key}'.")
        if name not in table:
            bad("section_unknown", f"'{name}' is not a section of the document.")
        elif table[name][0] != feature.model:
            bad("section_foreign", f"'{name}' belongs to {table[name][0]}, not {feature.model}.")
    for name in sorted(set(owned) - set(sections)):
        bad("section_unclaimed", f"The document has the section '{name}' for this feature.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "event_as_code")


features.register_verifier("event_as_code", verify, facts=facts, static=static)
