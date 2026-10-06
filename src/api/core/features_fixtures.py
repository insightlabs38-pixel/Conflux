"""Verifier for the `fixtures` property (PD-F003-B03-T05): whether a scenario creates the feature.

Tests, demos and training start from deterministic synthetic events (`integrations.demo_scenarios`,
which the isolated browser fixtures also use): one real event built through the domain's own rules,
with the same ids for the same seed. A feature either appears in that event or says why not, and a
claim is held to the generator:

- `seeded:<scenario>`: the scenario exists (`scenario_archive` accepts it), so the claim names a
  real generator, and the proof (`test:<path>::<name>`) generates the event and finds rows of the
  feature's own model;
- `planned` (the contract's own state): the scenario does not create the feature yet and the owning
  task will add it; the same test proves the model has no rows today, so a planned claim that has
  since come true, or a seeded claim that is no longer true, fails;
- `not_applicable` with a reason: a demo must not invent this data (secrets, real people).

`tests/integration/test_feature_fixtures.py` builds the demo event and counts the rows of every
feature's model, in both directions. The report lists the scenario each feature appears in.
"""

import re

from . import features
from .features import problem

SCENARIO = "integrations.demo_scenarios"


def parse(claim):
    scenarios, tests, other = [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        if kind == "seeded":
            scenarios.append(rest)
        elif kind == "test":
            tests.append(rest)
        else:
            other.append(ref)
    return scenarios, tests, other


def scenario_exists(system, key: str) -> bool:
    build = system.resolve(f"{SCENARIO}:scenario_archive")
    fixed = system.resolve(f"{SCENARIO}:FIXED_AT")
    if build is None or fixed is None:
        return False
    try:
        build(key, at=fixed)
    except Exception:  # noqa: BLE001 - any refusal means the scenario is not a real one
        return False
    return True


def facts(feature, system) -> dict:
    claim = feature.claims.get("fixtures")
    if claim is None or claim.state != "provided":
        return {}
    scenarios, _, _ = parse(claim)
    return {"scenarios": scenarios}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="fixtures"))

    scenarios, tests, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not seeded:<scenario> or test:.")
    if not scenarios:
        bad("no_scenario", "Name the scenario that creates the feature (seeded:<scenario>).")
    if len(set(scenarios)) != len(scenarios):
        bad("scenario_twice", "A scenario is named twice.")
    if not tests:
        bad("no_test", "Name the test that generates the event (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    for name in scenarios:
        if not scenario_exists(system, name):
            bad("scenario_unknown", f"'{name}' is not a scenario the generator can build.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "fixtures")


features.register_verifier("fixtures", verify, facts=facts, static=static)
