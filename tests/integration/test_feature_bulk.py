"""PD-F003-B02-T03: the bulk claims of the completeness contract, held against the planner.

A feature either has actions in the one bulk planner (`communications.bulk`) or says why a batch
does not fit it. The verifier reads the registry and the handlers; these tests prove the claims
against the planner itself: every registered action belongs to exactly one claimed feature, and the
audit actions the claims name are exactly the ones a real preview and apply leaves behind."""

import pytest
from audit.models import AuditEvent
from communications import bulk
from core import features as ft
from core import features_bulk

from tests.integration.test_bulk_operations import case, operations, post, preview  # noqa: F401

pytestmark = pytest.mark.django_db


def claimed():
    found = {}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        actions, _, _, _ = features_bulk.parse(feature.claims["bulk"])
        for key, audit in actions:
            found.setdefault(key, []).append((feature.key, audit))
    return found


CLAIMED = claimed()


def test_every_registered_bulk_action_belongs_to_exactly_one_claimed_feature():
    assert set(bulk.ACTIONS) == set(CLAIMED)
    assert all(len(owners) == 1 for owners in CLAIMED.values())
    for feature in ft.FEATURES.values():
        claim = feature.claims["bulk"]
        actions, _, reasons, _ = features_bulk.parse(claim)
        assert bool(actions) != bool(reasons) or claim.state == "planned", feature.key


def test_the_audit_actions_the_claims_name_are_what_a_real_apply_records(case):  # noqa: F811
    ops = operations(case)
    assert {op["action"] for op in ops} == set(CLAIMED)
    token = preview(case, ops)
    assert post(case, ops, token).status_code == 200
    recorded = set(AuditEvent.objects.values_list("action", flat=True))
    named = {audit for owners in CLAIMED.values() for _, audit in owners}
    assert recorded - {"operations.bulk_applied"} == named


def test_the_report_says_what_each_action_takes_and_records():
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["project"]["facts"]["bulk"]["bulk_actions"] == [
        "move (Move projects to a track): takes projects, track; records project.track_moved"
    ]
    assert row["message"]["facts"]["bulk"]["bulk_actions"] == [
        "send (Send a message): takes audience_kind, body, subject, audience_params?; "
        "records message.sent"
    ]
    assert row["track"]["facts"]["bulk"]["bulk"] == "not offered"
    assert row["application"]["claims"]["bulk"]["state"] == "planned"


TEST = (
    "test:tests/integration/test_bulk_operations.py"
    "::test_full_preview_apply_and_retry_are_atomic_and_audited"
)
SEND = "action:send=message.sent"
MOVE = "action:move=project.track_moved"


def verify(feature_key, refs):
    base = ft.FEATURES[feature_key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, {"bulk": claim})
    return ft.VERIFIERS["bulk"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


def test_the_real_claims_verify_clean():
    assert verify("message", (SEND, TEST)) == []
    assert verify("track", ("no_bulk@tracks are few and ordered in place on the dashboard",)) == []


@pytest.mark.parametrize(
    ("feature", "refs", "code"),
    [
        ("track", ("no_bulk@short",), "no_reason"),
        ("track", (SEND, TEST, "no_bulk@a batch does not fit this feature at all"), "both"),
        ("message", (TEST,), "no_action"),
        ("message", (SEND,), "no_test"),
        ("message", (SEND, "test:nowhere"), "test_ref"),
        ("message", ("action:send", TEST), "audit_shape"),
        ("message", ("action:teleport=message.sent", TEST), "action_unknown"),
        ("message", ("action:send=message.sent", "action:send=message.sent", TEST), "action_twice"),
        ("message", ("action:send=message.vanished", TEST), "audit_unknown"),
        ("message", ("action:send=stage.advanced", TEST), "audit_foreign"),
        ("project", ("action:move=project.updated", TEST), "audit_not_written"),
        ("project", (MOVE, TEST, "color:red"), "bad_ref"),
        ("track", (MOVE, TEST), "action_shared"),
    ],
)
def test_each_bulk_failure_has_a_code(feature, refs, code):
    assert code in codes(verify(feature, refs))


def test_the_ci_check_finds_a_proof_that_does_not_exist(tmp_path):
    feature = ft.Feature("m", "M", "communications.Message", {})
    claim = ft.provided(SEND, "test:tests/integration/test_nothing.py::test_gone")
    assert {p["code"] for p in features_bulk.static(feature, claim, tmp_path)} == {"test_file"}
