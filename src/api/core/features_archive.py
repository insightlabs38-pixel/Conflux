"""Verifier for the `archive` property (PD-F003-B02-T08): a feature's place in an archive.

An event is archived and restored through one frozen contract (`integrations.final_archive_schema`,
`TABLES`): the tables written, how each is reached from the event and which fields travel. Every
event-owned model is classified there or in the archive's exclusion list
(`tests/integration/test_final_archive.py`), so the contract already refuses an unclassified model;
what this property adds is each feature's own answer. A `provided` claim says one of:

- `table:<app.model>`: the feature's own model is one of the archive's tables (the label is the
  lowercase model label), so it is exported with the event and restored into a new one. The report
  lists how the table is reached and which fields travel;
- `root@<reason>`: the feature is the event itself, which is the thing archived and restored as a
  new draft event (only `events.Event` may say so);
- `excluded@<reason>`: the model is deliberately not archived (a secret, runtime traffic, content
  that is not part of the event's record), and why. It must not be in `TABLES`.

and names the proof, `test:<path>::<name>`, a test that restores an archive and finds the table's
rows again (CI checks it exists). A model that is both claimed `excluded` and archived, or claimed
`table` and absent from the contract, is refused. `tests/integration/test_feature_archive.py`
proves each table claim by restoring a real archive and each excluded claim against the archive's
exclusion list.
"""

import re

from . import features
from .features import problem

MIN_REASON = 20
SCHEMA = "integrations.final_archive_schema:TABLES"
ROOT = "events.Event"


def parse(claim):
    tables, roots, excluded, tests, other = [], [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "table":
            tables.append(rest)
        elif kind == "test":
            tests.append(rest)
        elif head == "root":
            roots.append(reason)
        elif head == "excluded":
            excluded.append(reason)
        else:
            other.append(ref)
    return tables, roots, excluded, tests, other


def contract(system) -> dict:
    return dict(system.resolve(SCHEMA) or {})


def facts(feature, system) -> dict:
    claim = feature.claims.get("archive")
    if claim is None or claim.state != "provided":
        return {}
    tables, roots, excluded, _, _ = parse(claim)
    if roots:
        return {"archive": "the event itself", "why": roots[0]}
    if excluded:
        return {"archive": "not archived", "why": excluded[0]}
    table = contract(system)
    rows = []
    for label in tables:
        if label not in table:
            continue
        scope, fields, omitted = table[label]
        rows.append(f"{label}: reached by {scope}, {len(fields.split())} fields")
        if omitted:
            rows.append(f"left out of {label}: {', '.join(omitted.split())}")
    return {"tables": rows}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="archive"))

    tables, roots, excluded, tests, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not table:<model>, root@, excluded@ or test:.")
    kinds = [bool(tables), bool(roots), bool(excluded)]
    if sum(kinds) != 1:
        bad("one_answer", "Say exactly one of table:<model>, root@<reason> or excluded@<reason>.")
        return found
    if not tests:
        bad("no_test", "Name the test that proves it (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    schema = contract(system)
    if not schema:
        bad("contract_missing", f"The archive contract '{SCHEMA}' cannot be read.")
        return found
    mine = feature.model.lower()
    for answer in (*roots, *excluded):
        if len(answer.strip()) < MIN_REASON:
            bad("no_reason", "Say why (a short sentence).")
    if roots:
        if feature.model != ROOT:
            bad("root_foreign", f"Only {ROOT} is the root of the archive, not {feature.model}.")
        if len(roots) > 1:
            bad("no_reason", "Say it once.")
    if excluded:
        if len(excluded) > 1:
            bad("no_reason", "Say it once.")
        if mine in schema:
            bad(
                "archived_but_excluded", f"{mine} is a table of the archive, so it is not excluded."
            )
    if tables:
        if tables != [mine]:
            bad("table_foreign", f"Claim the feature's own model only: table:{mine}.")
        for label in tables:
            if label not in schema:
                bad("table_unknown", f"'{label}' is not a table of the archive contract.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "archive")


features.register_verifier("archive", verify, facts=facts, static=static)
