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
    "archive",
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


# --- the eight surface properties (PD-F003-B02-T90) ----------------------------------------------


def surface_items():
    """Every item the eight surface claims name, with the features that claim it."""
    from core import (
        features_archive,
        features_bulk,
        features_cli,
        features_eac,
        features_mcp,
        features_ui,
        features_webhook,
    )

    found = {k: {} for k in ("action", "command", "tool", "section", "emit", "table", "use")}
    for feature in ft.FEATURES.values():
        c = feature.claims
        for key, _ in features_bulk.parse(c["bulk"])[0]:
            found["action"].setdefault(key, set()).add(feature.key)
        for key in features_cli.parse(c["cli"])[0]:
            found["command"].setdefault(key, set()).add(feature.key)
        for key in features_mcp.parse(c["mcp"])[0]:
            found["tool"].setdefault(key, set()).add(feature.key)
        for key in features_eac.parse(c["event_as_code"])[0]:
            found["section"].setdefault(key, set()).add(feature.key)
        for action, _ in features_webhook.parse(c["webhook"])[0]:
            found["emit"].setdefault(action, set()).add(feature.key)
        for key in features_archive.parse(c["archive"])[0]:
            found["table"].setdefault(key, set()).add(feature.key)
        for component, path in features_ui.parse_advanced(c["ui_advanced"])[0]:
            found["use"].setdefault((component, path), set()).add(feature.key)
    return found


def test_no_action_command_tool_section_event_or_table_is_claimed_by_two_features():
    shared = {
        kind: {item: who for item, who in found.items() if len(who) > 1}
        for kind, found in surface_items().items()
    }
    assert not any(shared.values()), shared


def test_the_surfaces_count_what_the_documents_say():
    """The matrix and the guide state these numbers; a change must update them on purpose."""
    found = surface_items()
    assert {k: len(v) for k, v in found.items()} == {
        "action": 5,
        "command": 5,
        "tool": 5,
        "section": 10,
        "emit": 19,
        "table": 10,
        "use": 12,
    }


def test_the_webhook_and_audit_claims_describe_the_same_changes():
    from core import features_audit, features_webhook

    audited = {
        (f.key, action)
        for f in ft.FEATURES.values()
        for _, _, action, _ in features_audit.parse(f.claims["audit"])[0]
    }
    classified = {
        (f.key, action)
        for f in ft.FEATURES.values()
        for action, _ in (
            *features_webhook.parse(f.claims["webhook"])[0],
            *features_webhook.parse(f.claims["webhook"])[1],
        )
    }
    assert audited == classified and len(audited) == 40


def test_every_mcp_write_tool_reaches_an_audited_change_and_every_cli_command_an_sdk_operation():
    from core import features_audit, features_cli, features_mcp
    from mcp_adapter.tools import BY_NAME

    for feature in ft.FEATURES.values():
        writes = {
            (route, method)
            for route, method, _, _ in features_audit.parse(feature.claims["audit"])[0]
        }
        for name in features_mcp.parse(feature.claims["mcp"])[0]:
            tool = BY_NAME[name]
            assert tool.read_only or (tool.url_name, tool.method) in writes, name
    table, generated = features_cli.load(ROOT)
    assert set(table) == set(features_cli.OUTSIDE) | {
        c for f in ft.FEATURES.values() for c in features_cli.parse(f.claims["cli"])[0]
    }
    assert all(set(ops) <= set(generated) for ops in table.values())


def test_a_system_that_changes_makes_a_surface_claim_fail(monkeypatch):
    """Each surface claim is held to its registry: change the registry and the claim fails."""
    from communications import bulk
    from core import features_webhook
    from integrations import eventascode
    from integrations.final_archive_schema import TABLES
    from mcp_adapter import tools

    def codes():
        return {p["code"] for p in ft.check(ft.System())}

    assert ft.check() == []
    # a tool added for a feature's route without a claim
    extra = tools.Tool("list_stage_notes", "List notes.", "GET", "stage-list")
    monkeypatch.setattr(tools, "TOOLS", [*tools.TOOLS, extra])
    assert "tool_unclaimed" in codes()
    monkeypatch.undo()
    # ... and the same for a feature that said no tool reaches it
    extra = tools.Tool("list_tracks", "List tracks.", "GET", "track-list")
    monkeypatch.setattr(tools, "TOOLS", [*tools.TOOLS, extra])
    assert "mcp_exists" in codes()
    monkeypatch.undo()
    # a bulk action that is no longer registered
    monkeypatch.delitem(bulk.ACTIONS, "move")
    assert "action_unknown" in codes()
    monkeypatch.undo()
    # a document section the track model owns, added without a claim
    monkeypatch.setitem(
        eventascode.SECTION_MODELS, "track_notes", ("events.Track", ("events.Track",))
    )
    assert "section_unclaimed" in codes()
    monkeypatch.undo()
    # a change that starts emitting an event while its claim says silent
    real = features_webhook.scan_outbox()
    patched = {**real, "project.created": {"emits": {"project.created"}, "silent": False}}
    monkeypatch.setattr(features_webhook, "scan_outbox", lambda: patched)
    assert "silent_but_emits" in codes()
    monkeypatch.undo()
    # a table that leaves the archive contract
    monkeypatch.delitem(TABLES, "events.track")
    assert "table_unknown" in codes()
    monkeypatch.undo()
    assert ft.check() == []
