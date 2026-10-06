"""PD-F003-B02-T06: the Event-as-Code claims of the completeness contract, held against the module.

A feature either is a section of the configuration document or says why it is not. The verifier
reads the module's section table; these tests prove the table against the code: every section is
claimed by exactly one feature or named as owned by none, and an apply writes exactly the rows each
section declares (and nothing of a feature that says it is runtime participant data)."""

import pytest
from core import features as ft
from core import features_eac
from django.apps import apps
from events.models import Event
from integrations import eventascode
from integrations.demo_scenarios import generate_demo_event
from test_sponsor_portal import client_for

from tests.integration.test_event_as_code import call, doc_of

pytestmark = pytest.mark.django_db

BOOKKEEPING = {"audit.AuditEvent", "audit.DomainEvent"}  # every apply is audited


def claimed():
    found = {}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        sections, _, _, _ = features_eac.parse(feature.claims["event_as_code"])
        for name in sections:
            found.setdefault(name, []).append(feature.key)
    return found


CLAIMED = claimed()


def test_every_document_section_is_claimed_by_exactly_one_feature_or_named_as_outside():
    assert set(eventascode.SECTION_MODELS) == {"event", *eventascode.SECTIONS}
    assert set(eventascode.SECTION_MODELS) == set(CLAIMED) | set(features_eac.OUTSIDE)
    assert all(len(owners) == 1 for owners in CLAIMED.values())
    assert not set(CLAIMED) & set(features_eac.OUTSIDE)
    assert all(len(r) >= features_eac.MIN_REASON for r in features_eac.OUTSIDE.values())
    models = {f.model for f in ft.FEATURES.values()}
    for name in features_eac.OUTSIDE:  # owned by a model that no feature covers
        assert eventascode.SECTION_MODELS[name][0] not in models, name
    for model in {m for owner, written in eventascode.SECTION_MODELS.values() for m in written}:
        assert apps.get_model(model)


def test_the_registry_is_clean_with_the_event_as_code_claims():
    assert ft.check() == []


def counts():
    return {m._meta.label: m.objects.count() for m in apps.get_models() if not m._meta.proxy}


def test_every_section_writes_exactly_the_rows_it_declares():
    source = generate_demo_event(seed=51, participants=4, judges=2)
    organizer = source.workspace.memberships.get(role="organizer").user
    document = doc_of(source)
    target = Event.objects.create(workspace=source.workspace, name="Blank", slug="blank")
    client = client_for(organizer)
    before = counts()
    applied = call(
        client,
        target,
        "apply/",
        document=document,
        expected_digest=eventascode.digest(target),
    )
    assert applied.status_code == 200, applied.content
    after = counts()
    changed = {label for label in after if after[label] != before[label]} - BOOKKEEPING
    declared = {
        model
        for name, (_, written) in eventascode.SECTION_MODELS.items()
        if document.get(name) not in (None, [], {})
        for model in written
    }
    assert changed == declared - {"events.Event"}  # the event itself is updated, not created
    assert document["tracks"] and document["stages"] and document["awards"]


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"event_as_code": claim})
    return ft.VERIFIERS["event_as_code"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_eac.py"
    "::test_every_section_writes_exactly_the_rows_it_declares"
)


def test_the_real_claims_verify_clean_and_the_report_lists_the_sections():
    assert verify("track", ("section:tracks", TEST)) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["stage"]["facts"]["event_as_code"]["sections"] == [
        "stages: stages.Stage",
        "stage_transitions: stages.StageTransition",
    ]
    assert row["project"]["facts"]["event_as_code"]["eac"] == "not in the document"


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("project", ("no_eac@short",), "no_reason"),
        ("track", ("section:tracks", TEST, "no_eac@a reason long enough to be a sentence"), "both"),
        ("track", (TEST,), "no_section"),
        ("track", ("section:tracks",), "no_test"),
        ("track", ("section:tracks", "test:nowhere"), "test_ref"),
        ("track", ("section:tracks", TEST, "color:red"), "bad_ref"),
        ("track", ("section:tracks", "section:tracks", TEST), "section_twice"),
        ("track", ("section:nothing", TEST), "section_unknown"),
        ("track", ("section:stages", TEST), "section_foreign"),
        ("stage", ("section:stages", TEST), "section_unclaimed"),
        ("stage", ("no_eac@a reason long enough to be a sentence",), "eac_exists"),
        ("stage", ("section:stages", "section:stage_transitions", TEST), "ok"),
    ],
)
def test_each_event_as_code_failure_has_a_code(key, refs, code):
    found = codes(verify(key, refs))
    assert (not found) if code == "ok" else code in found


def test_a_section_may_not_be_claimed_by_two_features():
    found = codes(verify("form", ("section:forms", "section:tracks", TEST)))
    assert {"section_shared", "section_foreign"} <= found
