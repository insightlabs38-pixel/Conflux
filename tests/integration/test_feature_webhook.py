"""PD-F003-B02-T07: the webhook claims of the completeness contract, held against the outbox.

Every audited change of a feature either writes the outbox event its claim names (a `DomainEvent`
of that type, in the same transaction as the change, which subscribers receive as a signed webhook)
or is silent and writes none. This file sends each audited change through the API as the role that
may make it and reads the outbox, and shows a refused change leaves nothing behind."""

import pytest
from audit.models import AuditEvent, DomainEvent
from core import features as ft
from core import features_webhook

from tests.integration import test_feature_audit as harness
from tests.integration.test_feature_audit import DECLARED, scenarios, send

pytestmark = pytest.mark.django_db

world = harness.world  # the audit suite's fixture: one workspace, every role, every scenario


def classified():
    """action -> ("emit", event type) or ("silent", reason), from every feature's claim."""
    found = {}
    for feature in ft.FEATURES.values():
        emits, silent, _, _ = features_webhook.parse(feature.claims["webhook"])
        found |= {action: ("emit", event_type) for action, event_type in emits}
        found |= {action: ("silent", reason) for action, reason in silent}
    return found


CLAIMED = classified()


def test_every_audited_change_is_classified_and_nothing_else_is():
    assert {action for _, _, _, action in DECLARED} == set(CLAIMED)
    assert ft.check() == []


@pytest.mark.parametrize(
    ("key", "route", "method", "action"),
    DECLARED,
    ids=[f"{k}:{r}:{m}" for k, r, m, _ in DECLARED],
)
def test_each_audited_change_writes_the_outbox_event_its_claim_names(
    world, key, route, method, action
):
    who, kwargs, body = scenarios(world)[(route, method)]()
    before_events = DomainEvent.objects.count()
    before_audit = AuditEvent.objects.count()
    response = send(world, route, method, who, kwargs, body)
    assert response.status_code in (200, 201, 204), (route, method, response.content[:300])
    rows = list(DomainEvent.objects.order_by("id")[before_events:])
    audit = [r for r in AuditEvent.objects.order_by("id")[before_audit:] if r.action == action]
    assert audit, f"{method} {route} did not audit {action}"
    kind, value = CLAIMED[action]
    if kind == "emit":
        mine = [row for row in rows if row.event_type == value]
        assert mine, f"{method} {route} wrote {[r.event_type for r in rows]}, not {value}"
        assert all(row.workspace_id == world["workspace"].id for row in mine)
        assert mine[0].status == "pending" if hasattr(mine[0], "status") else True
    else:
        assert rows == [], (
            f"{method} {route} is claimed silent but wrote {[r.event_type for r in rows]}"
        )


@pytest.mark.parametrize(
    ("key", "route", "method", "action"),
    DECLARED,
    ids=[f"{k}:{r}:{m}" for k, r, m, _ in DECLARED],
)
def test_a_refused_change_leaves_nothing_in_the_outbox(world, key, route, method, action):
    who, kwargs, body = scenarios(world)[(route, method)]()
    world["people"]["intruder"] = harness.user("intruder")
    before = DomainEvent.objects.count()
    response = send(world, route, method, "intruder", kwargs, body)
    assert response.status_code in (401, 403, 404)
    assert DomainEvent.objects.count() == before


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"webhook": claim})
    return ft.VERIFIERS["webhook"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_webhook.py"
    "::test_each_audited_change_writes_the_outbox_event_its_claim_names"
)
REASON = "a reason that is long enough to be a sentence"


def real(key):
    return list(ft.FEATURES[key].claims["webhook"].refs)


def test_the_real_claims_verify_clean_and_the_report_lists_events_and_silence():
    assert verify("track", real("track")) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["track"]["facts"]["webhook"]["emits"] == [
        "track.created → track.created",
        "track.deleted → track.deleted",
        "track.updated → track.updated",
    ]
    assert row["project"]["facts"]["webhook"]["silent"] == ["project.created", "project.updated"]


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", [TEST], "unclassified"),
        ("track", real("track") + ["silent:track.created@" + REASON], "classified_twice"),
        ("track", [r for r in real("track") if "track.deleted" not in r], "unclassified"),
        ("track", real("track") + ["emit:stage.created=stage.created"], "action_not_audited"),
        ("track", real("track") + ["silent:stage.created@" + REASON], "action_not_audited"),
        ("track", real("track") + ["color:red"], "bad_ref"),
        ("track", [r for r in real("track") if not r.startswith("test:")], "no_test"),
        ("track", real("track") + ["test:nowhere"], "test_ref"),
        (
            "track",
            [r.replace("=track.created", "=Track.Created") for r in real("track")],
            "type_shape",
        ),
        (
            "track",
            [r.replace("=track.created", "=track.removed") for r in real("track")],
            "emit_not_recorded",
        ),
        (
            "track",
            [
                "silent:track.created@" + REASON if r.startswith("emit:track.created") else r
                for r in real("track")
            ],
            "silent_but_emits",
        ),
        (
            "project",
            [
                "silent:project.created@short" if "project.created" in r else r
                for r in real("project")
            ],
            "no_reason",
        ),
    ],
)
def test_each_webhook_failure_has_a_code(key, refs, code):
    assert code in codes(verify(key, refs))


def test_the_outbox_scan_reads_helpers_direct_calls_and_silence():
    scanned = features_webhook.scan_outbox()
    assert scanned["track.created"]["emits"] == {"track.created"}  # through a helper
    assert scanned["event.status_changed"]["emits"] == {"event.status_changed"}  # a direct call
    assert scanned["project.created"] == {"emits": set(), "silent": True}
    assert scanned["temporal_gate.updated"]["emits"] == {"temporal_gate.updated"}
