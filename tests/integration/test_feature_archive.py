"""PD-F003-B02-T08: the archive claims of the completeness contract, held against a real restore.

An event is archived and restored through one frozen contract (`TABLES`). A feature either has its
own model among those tables, is the event itself (the root), or says why it is not archived. The
verifier reads the contract; these tests prove the claims: each claimed table is exported with its
rows and restored into a new event with the same number of rows, each excluded model is on the
archive's own exclusion list and not in its contract, and every feature says one of the three."""

import pytest
from core import features as ft
from core import features_archive
from django.apps import apps
from events.models import Event, Track
from forms.models import FormDefinition
from integrations.archive import build_archive
from integrations.final_archive_schema import TABLES
from policies.models import Policy

from tests.integration.test_final_archive import EXCLUDED_EVENT_MODELS, restore, source

pytestmark = pytest.mark.django_db


def answers():
    found = {"table": {}, "root": [], "excluded": {}}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        tables, roots, excluded, _, _ = features_archive.parse(feature.claims["archive"])
        for label in tables:
            found["table"][feature.key] = label
        if roots:
            found["root"].append(feature.key)
        if excluded:
            found["excluded"][feature.key] = feature.model.lower()
    return found


ANSWERS = answers()


def test_every_feature_says_exactly_one_thing_about_the_archive():
    claimed = set(ANSWERS["table"]) | set(ANSWERS["root"]) | set(ANSWERS["excluded"])
    assert claimed == set(ft.FEATURES)
    assert len(ANSWERS["table"]) + len(ANSWERS["root"]) + len(ANSWERS["excluded"]) == len(claimed)
    assert ANSWERS["root"] == ["event"]
    assert ft.check() == []


def test_each_excluded_model_is_in_the_archives_exclusion_list_and_not_in_its_contract():
    for key, label in ANSWERS["excluded"].items():
        assert label in EXCLUDED_EVENT_MODELS, key
        assert label not in TABLES, key
    for label in ANSWERS["table"].values():
        assert label in TABLES and label not in EXCLUDED_EVENT_MODELS


def test_each_claimed_table_is_restored_with_its_rows():
    workspace, event, *_ = source()
    Track.objects.create(event=event, name="Open track")
    FormDefinition.objects.create(event=event, name="Application", draft_schema={"fields": []})
    Policy.objects.create(event=event, name="Open policy", ast={"op": "true"})
    archive = build_archive(event, mode="final")
    copied = restore(workspace, archive)
    assert copied.pk != event.pk
    for key, label in ANSWERS["table"].items():
        model = apps.get_model(label)
        scope = TABLES[label][0]
        original = model.objects.filter(**{scope: event}).count()
        restored = model.objects.filter(**{scope: copied}).count()
        assert original >= 1, f"{key}: the source event has no {label} row to prove it with"
        assert len(archive["tables"][label]) == original, label
        assert restored == original, f"{key}: {label} restored {restored} of {original}"


def test_the_event_is_the_root_and_restores_as_a_new_draft_event():
    workspace, event, *_ = source()
    copied = restore(workspace, build_archive(event, mode="final"))
    assert isinstance(copied, Event) and copied.pk != event.pk
    assert copied.status == "draft" and not copied.is_public
    assert "events.event" not in TABLES  # the event is the container, not a table


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"archive": claim})
    return ft.VERIFIERS["archive"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_archive.py"
    "::test_each_claimed_table_is_restored_with_its_rows"
)
REASON = "a reason that is long enough to be a sentence"


def test_the_real_claims_verify_clean_and_the_report_lists_what_travels():
    assert verify("track", ("table:events.track", TEST)) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["track"]["facts"]["archive"]["tables"] == [
        "events.track: reached by event, 4 fields"
    ]
    assert row["event"]["facts"]["archive"]["archive"] == "the event itself"
    assert row["message"]["facts"]["archive"]["archive"] == "not archived"
    assert any(
        "left out of" in line for line in row["evaluation_plan"]["facts"]["archive"]["tables"]
    )


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", (TEST,), "one_answer"),
        ("track", ("table:events.track", "excluded@" + REASON, TEST), "one_answer"),
        ("track", ("table:events.track",), "no_test"),
        ("track", ("table:events.track", "test:nowhere"), "test_ref"),
        ("track", ("table:events.track", TEST, "color:red"), "bad_ref"),
        ("track", ("excluded@short", TEST), "no_reason"),
        ("track", ("excluded@" + REASON, TEST), "archived_but_excluded"),
        ("track", ("table:stages.stage", TEST), "table_foreign"),
        ("track", ("table:events.track", "table:stages.stage", TEST), "table_foreign"),
        ("event", ("table:events.event", TEST), "table_unknown"),
        ("track", ("root@" + REASON, TEST), "root_foreign"),
        ("message", ("table:communications.message", TEST), "table_unknown"),
        ("event", ("root@short", TEST), "no_reason"),
    ],
)
def test_each_archive_failure_has_a_code(key, refs, code):
    assert code in codes(verify(key, refs))


def test_an_excluded_and_a_root_claim_that_are_honest_verify_clean():
    assert verify("message", ("excluded@" + REASON, TEST)) == []
    assert verify("event", ("root@" + REASON, TEST)) == []
