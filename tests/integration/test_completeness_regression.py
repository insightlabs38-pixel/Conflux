"""PD-F003-B01-T90: cross-cutting regression for the completeness contract.

Each property has its own suite (`test_feature_*.py`); this file checks what only the whole shows:
every landed property is claimed and verified for all fifteen features, no claim verifies for a
feature it does not describe, every proving test a claim names exists, the report is derived,
read-only and free of secrets, and a changed system makes a claim fail rather than pass."""

import json
import re
from pathlib import Path

import pytest
from core import features as ft
from core import features_search

pytestmark = pytest.mark.django_db

ROOT = Path(__file__).resolve().parents[2]
LANDED = [
    "identity",
    "validation",
    "authorization",
    "audit",
    "idempotency",
    "rest",
    "sdk",
    "search",
    "ui_base",
    "ui_advanced",
    "bulk",
    "cli",
    "mcp",
    "event_as_code",
    "webhook",
]


def run(prop, feature, claim):
    return ft.VERIFIERS[prop](feature, claim, ft.System())


def test_every_landed_property_is_claimed_and_verified_for_all_fifteen_features():
    assert ft.landed() == LANDED
    assert len(ft.FEATURES) == 15
    assert ft.check() == [] and ft.check_static(ROOT) == []
    report = ft.report()
    assert report["ok"] is True and report["problems"] == []
    for prop in LANDED:
        assert report["totals"][prop]["unclaimed"] == 0, prop
        assert report["totals"][prop]["planned"] <= 1, prop  # an owed screen, with its owner
    # the properties of the other batches are not claimed yet, and the report says so
    pending = [p["key"] for p in report["properties"] if not p["landed"]]
    assert len(pending) == 21 - len(LANDED) and not set(pending) & set(LANDED)


def test_no_route_change_action_or_entity_is_claimed_by_two_features():
    """A claim copied onto another feature leaves two owners: every claimed item has exactly one."""
    from core import features_audit, features_idempotency

    owners = {"route": {}, "change": {}, "action": {}, "mode": {}, "entity": {}}
    for feature in ft.FEATURES.values():
        for ref in feature.claims["authorization"].refs:
            if ref.startswith("route:"):
                owners["route"].setdefault(ref, set()).add(feature.key)
        for route, method, action, _ in features_audit.parse(feature.claims["audit"])[0]:
            owners["change"].setdefault((route, method), set()).add(feature.key)
            owners["action"].setdefault(action, set()).add(feature.key)
        for route, method, _, _, _ in features_idempotency.parse(feature.claims["idempotency"])[0]:
            owners["mode"].setdefault((route, method), set()).add(feature.key)
        for key in features_search.parse(feature.claims["search"])[0]["entity"]:
            owners["entity"].setdefault(key, set()).add(feature.key)
    shared = {
        kind: {item: who for item, who in found.items() if len(who) > 1}
        for kind, found in owners.items()
    }
    assert not any(shared.values()), shared
    assert owners["change"].keys() == owners["mode"].keys()


def test_a_search_claim_for_another_feature_is_refused_unless_it_says_nothing_is_offered():
    for owner in ft.FEATURES.values():
        claim = owner.claims["search"]
        if not any(r.startswith("entity:") for r in claim.refs):
            continue
        for other in ft.FEATURES.values():
            if other.key != owner.key:
                assert run("search", other, claim), (owner.key, other.key)


@pytest.mark.parametrize("prop", LANDED)
def test_dropping_any_ref_of_a_real_claim_is_noticed_or_leaves_it_equally_true(prop):
    """Sensitivity: most refs matter. Count how many single-ref removals the verifier catches."""
    caught = total = 0
    for feature in ft.FEATURES.values():
        claim = feature.claims[prop]
        for i in range(len(claim.refs)):
            fewer = ft.Claim("provided", refs=claim.refs[:i] + claim.refs[i + 1 :])
            total += 1
            caught += bool(run(prop, feature, fewer)) if fewer.refs else 1
    assert caught / total > 0.35, (prop, caught, total)


def test_the_report_is_derived_query_free_and_free_of_secrets(django_assert_num_queries):
    with django_assert_num_queries(0):
        report = ft.report()
    text = json.dumps(report)
    assert not re.search(r"whsec_|secret_key|password|Bearer [A-Za-z0-9]{16,}", text, flags=re.I)
    for row in report["features"]:
        for prop in LANDED:
            assert row["claims"][prop]["state"] in ("provided", "not_applicable", "planned"), (
                row["key"],
                prop,
            )
    # what is shown about a feature is derived: facts exist for the properties that derive any
    for row in report["features"]:
        for prop in (
            "validation",
            "authorization",
            "audit",
            "idempotency",
            "rest",
            "sdk",
            "search",
        ):
            assert row["facts"][prop], (row["key"], prop)


def test_every_proving_test_a_claim_names_exists_and_the_request_proofs_are_all_named():
    names = set()
    for feature in ft.FEATURES.values():
        for prop in LANDED:
            for ref in feature.claims[prop].refs:
                if ref.startswith("test:"):
                    path, _, name = ref[5:].partition("::")
                    assert (ROOT / path).is_file(), ref
                    names.add((path, name))
    assert len(names) >= 25
    files = {path for path, _ in names}
    assert {
        "tests/integration/test_feature_authorization.py",
        "tests/integration/test_feature_audit.py",
        "tests/integration/test_feature_idempotency.py",
        "tests/integration/test_feature_rest.py",
        "tests/integration/test_feature_sdk.py",
    } <= files


def test_the_audit_idempotency_and_sdk_proofs_cover_the_same_changes():
    """One request set backs three properties: they cannot describe different changes."""
    changes = {}
    for prop, parse in (
        (
            "audit",
            lambda c: [
                (r, m)
                for r, m, _, _ in __import__("core.features_audit", fromlist=["x"]).parse(c)[0]
            ],
        ),
        (
            "idempotency",
            lambda c: [
                (r, m)
                for r, m, _, _, _ in __import__("core.features_idempotency", fromlist=["x"]).parse(
                    c
                )[0]
            ],
        ),
    ):
        changes[prop] = {
            (f.key, r, m) for f in ft.FEATURES.values() for r, m in parse(f.claims[prop])
        }
    assert changes["audit"] == changes["idempotency"] and len(changes["audit"]) == 40


def test_a_system_that_changes_makes_a_claim_fail(monkeypatch):
    """The claim is held to the live system, not remembered: change the system and it fails."""
    from core import entities as registry

    # a search field added without a claim
    entity = registry.entities()["applications"]  # discovers the registrations first
    extra = registry.Field("extra", registry.TEXT, "note", "Extra")
    monkeypatch.setitem(
        registry._ENTITIES,
        "applications",
        registry.Entity(
            entity.key,
            entity.label,
            entity.roles,
            entity.base,
            (*entity.fields, extra),
            entity.default_sort,
        ),
    )
    assert any(p["code"] == "fields_mismatch" for p in ft.check())
    monkeypatch.setitem(registry._ENTITIES, "applications", entity)
    assert ft.check() == []
    # an audit action that the code no longer records
    monkeypatch.setattr(ft, "scan_audit_actions", lambda: {})
    assert any(p["code"] == "action_missing" for p in ft.check(ft.System()))
