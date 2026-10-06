"""PD-F003-B03-T05: the fixture claims of the completeness contract, held against a real scenario.

The demo generator builds one deterministic event through the domain's own rules. A feature either
appears in it (`seeded`), is owed to it by a named task (`planned`) or is not something a demo may
invent (`not_applicable`). The verifier reads the generator; these tests build the event and count
the rows of every feature's model in both directions, so a feature that starts being seeded, or one
that stops, fails until its claim says so."""

import pytest
from core import features as ft
from core import features_fixtures
from django.apps import apps
from integrations.demo_scenarios import generate_demo_event

pytestmark = pytest.mark.django_db


def rows(event=None):
    return {key: apps.get_model(f.model).objects.count() for key, f in ft.FEATURES.items()}


def test_the_demo_scenario_creates_exactly_the_features_the_claims_say():
    generate_demo_event(seed=51, participants=4, judges=2)
    counted = rows()
    for key, feature in sorted(ft.FEATURES.items()):
        claim = feature.claims["fixtures"]
        if claim.state == "provided":
            assert counted[key] > 0, f"{key} is claimed seeded but the scenario creates none"
        else:
            assert counted[key] == 0, f"{key} is claimed {claim.state} but the scenario seeds it"
    seeded = {k for k, f in ft.FEATURES.items() if f.claims["fixtures"].state == "provided"}
    assert seeded == {
        "application",
        "award",
        "evaluation_plan",
        "event",
        "project",
        "stage",
        "submission",
        "team",
        "track",
    }


def test_the_same_seed_gives_the_same_event_and_a_planned_owner_exists():
    first = generate_demo_event(seed=51, participants=4, judges=2)
    again_ids = first.public_id
    from integrations.demo_scenarios import demo_public_ids

    assert demo_public_ids("hackathon", 51)[1] == again_ids
    planned = {
        f.claims["fixtures"].owner
        for f in ft.FEATURES.values()
        if f.claims["fixtures"].state == "planned"
    }
    assert planned == {"PD-S061-B02-T01"}
    assert ft.check() == []


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"fixtures": claim})
    return ft.VERIFIERS["fixtures"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_fixtures.py"
    "::test_the_demo_scenario_creates_exactly_the_features_the_claims_say"
)


def test_the_real_claims_verify_clean_and_the_report_lists_the_scenario():
    assert verify("track", ["seeded:hackathon", TEST]) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["track"]["facts"]["fixtures"] == {"scenarios": ["hackathon"]}
    assert row["message"]["claims"]["fixtures"]["state"] == "planned"
    assert row["webhook"]["claims"]["fixtures"]["state"] == "not_applicable"


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        ([TEST], "no_scenario"),
        (["seeded:hackathon"], "no_test"),
        (["seeded:hackathon", "test:nowhere"], "test_ref"),
        (["seeded:hackathon", TEST, "color:red"], "bad_ref"),
        (["seeded:hackathon", "seeded:hackathon", TEST], "scenario_twice"),
        (["seeded:wedding", TEST], "scenario_unknown"),
    ],
)
def test_each_fixture_failure_has_a_code(refs, code):
    assert code in codes(verify("track", refs))


def test_the_scenario_check_reads_the_generator_not_a_list():
    system = ft.System()
    assert features_fixtures.scenario_exists(system, "hackathon") is True
    assert features_fixtures.scenario_exists(system, "wedding") is False
