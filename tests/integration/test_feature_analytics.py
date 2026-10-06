"""PD-F003-B03-T01: the analytics claims of the completeness contract, held against the summary.

The event summary (`operations/analytics/`) is computed from the domain's own tables. A feature
either is counted in it or says why not. The verifier reads the module and the response schema;
these tests prove the claims against a real event: every claimed measure is in the answer, every
claimed breakdown has exactly the keys of the field's choices, every section and every counted model
belongs to a claimed feature or is named as outside, and the numbers match the rows."""

import pytest
from core import features as ft
from core import features_analytics
from events.models import RegistrationStatus

from tests.integration.test_event_analytics import case, data, fixture, judging  # noqa: F401

pytestmark = pytest.mark.django_db


def claimed():
    found = {"section": {}, "measure": {}, "dimension": {}, "counted": {}}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        sections, measures, dimensions, _, reasons, _ = features_analytics.parse(
            feature.claims["analytics"]
        )
        if reasons:
            continue
        found["counted"][feature.model] = feature.key
        for name in sections:
            found["section"].setdefault(name, []).append(feature.key)
        for path in measures:
            found["measure"].setdefault(path, []).append(feature.key)
        for field, path in dimensions:
            found["dimension"][(feature.key, field)] = path
    return found


CLAIMED = claimed()


def walk(answer, path):
    for part in path.split("."):
        assert isinstance(answer, dict) and part in answer, f"{path}: no '{part}'"
        answer = answer[part]
    return answer


def test_every_summary_section_and_counted_model_is_claimed_or_named_as_outside():
    system = ft.System()
    assert set(CLAIMED["section"]) | set(features_analytics.OUTSIDE_SECTIONS) == (
        features_analytics.sections(system)
    )
    assert not set(CLAIMED["section"]) & set(features_analytics.OUTSIDE_SECTIONS)
    assert set(CLAIMED["counted"]) | set(features_analytics.OUTSIDE_MODELS) == (
        features_analytics.counted_models()
    )
    assert all(len(owners) == 1 for owners in CLAIMED["measure"].values())
    assert ft.check() == []


def test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event(case):  # noqa: F811
    people, stage, projects, submissions = fixture(case)
    judging(case, stage, projects)
    answer = data(case)
    for path in CLAIMED["measure"]:
        value = walk(answer, path)
        assert value is not None, path
    for (key, field), path in CLAIMED["dimension"].items():
        model = ft.System().model(ft.FEATURES[key].model)
        choices = {value for value, _ in model._meta.get_field(field).choices}
        assert set(walk(answer, path)) == choices, (key, field)
    # the numbers are the rows: four applications, two teams, three projects
    assert answer["registration"]["by_status"] == {
        **dict.fromkeys(RegistrationStatus.values, 0),
        "approved": 2,
        "pending": 1,
        "rejected": 1,
    }
    assert answer["registration"]["applications"] == 4
    assert answer["teams"]["total"] == 2 and answer["teams"]["with_members"] == 1
    assert answer["submissions"]["projects"] == 3
    assert answer["submissions"]["finalized_records"] == 1
    assert answer["judging"]["plan_count"] == 1


def test_an_empty_event_still_answers_every_claimed_measure(case):  # noqa: F811
    answer = data(case)
    for path in CLAIMED["measure"]:
        assert walk(answer, path) is not None, path


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"analytics": claim})
    return ft.VERIFIERS["analytics"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_analytics.py"
    "::test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event"
)
REASON = "a reason that is long enough to be a sentence"


def real(key):
    return list(ft.FEATURES[key].claims["analytics"].refs)


def test_the_real_claims_verify_clean_and_the_report_lists_sections_measures_and_breakdowns():
    assert verify("application", real("application")) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["application"]["facts"]["analytics"]
    assert facts["summary"] == ["registration"]
    assert facts["dimensions"] == ["status → registration.by_status"]
    assert "registration.approval" in facts["measures"]
    assert row["track"]["facts"]["analytics"]["analytics"] == "not counted"


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", ("no_analytics@short",), "no_reason"),
        ("team", real("team") + ["no_analytics@" + REASON], "both"),
        ("team", ["section:teams", TEST], "no_measure"),
        ("team", ["measure:teams.total", TEST], "one_section"),
        (
            "team",
            ["section:teams", "section:registration", "measure:teams.total", TEST],
            "one_section",
        ),
        ("team", ["section:teams", "measure:teams.total"], "no_test"),
        ("team", ["section:teams", "measure:teams.total", "test:nowhere"], "test_ref"),
        ("team", ["section:teams", "measure:teams.total", TEST, "color:red"], "bad_ref"),
        (
            "team",
            ["section:teams", "measure:teams.total", "measure:teams.total", TEST],
            "measure_twice",
        ),
        ("team", ["section:nothing", "measure:nothing.total", TEST], "section_unknown"),
        ("team", ["section:teams", "measure:registration.applications", TEST], "path_foreign"),
        ("team", ["section:teams", "measure:total", TEST], "path_shape"),
        (
            "team",
            ["section:teams", "measure:teams.total", "dimension:nothing=teams.total", TEST],
            "dimension_field",
        ),
        (
            "team",
            ["section:teams", "measure:teams.total", "dimension:name=teams.total", TEST],
            "dimension_choices",
        ),
        ("track", ["section:teams", "measure:teams.total", TEST], "model_not_counted"),
        ("team", ["no_analytics@" + REASON], "analytics_exists"),
        ("project", real("team"), "measure_shared"),
    ],
)
def test_each_analytics_failure_has_a_code(key, refs, code):
    assert code in codes(verify(key, refs))
