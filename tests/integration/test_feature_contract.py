"""PD-F003-B01-T01: the completeness contract's registry, report and identity verifier."""

import json
import pathlib

import pytest
import yaml
from accounts.models import Session, User
from audit.models import AuditEvent
from core import features as ft
from core import manifest
from django.test import Client
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEYS = [
    "announcement",
    "application",
    "artifact",
    "award",
    "evaluation_plan",
    "event",
    "form",
    "message",
    "policy",
    "project",
    "stage",
    "submission",
    "team",
    "track",
    "webhook",
]


def codes(found, prop=None):
    return sorted(p["code"] for p in found if prop in (None, p["property"]))


@pytest.fixture
def isolated(monkeypatch):
    """The real registry copied, so a test can add and break features."""
    monkeypatch.setattr(ft, "FEATURES", dict(ft.FEATURES))
    monkeypatch.setattr(ft, "VERIFIERS", dict(ft.VERIFIERS))
    return ft


def identity(*refs):
    return ft.provided(*(refs or ("field:public_id",)))


def only(feature_key="x", **over):
    """A registry holding one feature on a real model, ready to be made wrong."""
    values = {
        "key": feature_key,
        "label": "X",
        "model": "core.SavedView",
        "claims": {"identity": identity("field:public_id", "route:saved-view-detail")},
        "lifecycle": ft.Lifecycle("none", note="Edited in place."),
    }
    values.update(over)
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature(**values))
    # every other landed property must be claimed for the registry to be quiet about it
    return ft.check()


# --- the real system ----------------------------------------------------------------------------


def test_the_fifteen_features_agree_with_the_live_system():
    assert sorted(ft.FEATURES) == KEYS
    assert ft.check() == []
    assert ft.landed() == ["identity"]


def test_every_feature_resolves_to_its_model_and_a_uuid_public_id():
    system = ft.System()
    for feature in ft.FEATURES.values():
        model = system.model(feature.model)
        assert model is not None, feature.key
        assert ft.derived(feature, system)["id_type"] == "UUIDField", feature.key
        assert feature.claims["identity"].state == "provided"


def test_a_lifecycle_reads_its_states_from_the_models_own_choices():
    row = {f["key"]: f for f in ft.report()["features"]}
    assert [s["value"] for s in row["event"]["states"]] == ["draft", "open", "closed", "archived"]
    assert row["event"]["lifecycle"]["transitions"] == {
        "draft": ["open"],
        "open": ["closed"],
        "closed": ["archived"],
    }  # read from the code's own table, not copied
    assert row["event"]["lifecycle"]["terminal"] == ["archived"]
    assert [s["value"] for s in row["application"]["states"]] == [
        "pending",
        "approved",
        "waitlisted",
        "rejected",
    ]
    assert [s["value"] for s in row["award"]["states"]] == ["draft", "published"]
    assert row["track"]["lifecycle"]["kind"] == "none" and row["track"]["states"] == []


def test_a_models_own_status_field_cannot_be_left_undeclared():
    """Every status-like choice field of the fifteen models is covered by a choice lifecycle."""
    system = ft.System()
    for feature in ft.FEATURES.values():
        model = system.model(feature.model)
        status = [
            f.name
            for f in model._meta.get_fields()
            if getattr(f, "concrete", False)
            and f.name in ("status", "state", "phase")
            and f.choices
        ]
        if status:
            assert feature.lifecycle.kind == "choice" and feature.lifecycle.field == status[0]


def test_no_route_of_any_feature_uses_a_sequential_id():
    system = ft.System()
    for feature in ft.FEATURES.values():
        for ref in feature.claims["identity"].refs:
            if ref.startswith("route:"):
                assert not any(c == "int" for c, _ in system.converters(ref[6:])), ref


def test_the_report_is_deterministic_read_only_and_complete():
    before = AuditEvent.objects.count()
    first, second = ft.report(), ft.report()
    assert first == second and AuditEvent.objects.count() == before
    assert first["ok"] is True and first["problems"] == []
    assert [p["key"] for p in first["properties"]][:3] == [
        "identity",
        "validation",
        "authorization",
    ]
    assert len(first["properties"]) == 21 and first["totals"]["identity"] == {
        "provided": 15,
        "not_applicable": 0,
        "planned": 0,
        "unclaimed": 0,
    }
    assert first["totals"]["rest"]["unclaimed"] == 15  # not landed yet, so only unclaimed
    assert {p["key"]: p["landed"] for p in first["properties"]}["identity"] is True


def test_planned_claims_name_a_task_that_exists():
    tasks = {
        t["id"]
        for t in yaml.load((ROOT / "TASKS.yaml").read_text(), Loader=yaml.CSafeLoader)["tasks"]
    }
    for feature in ft.FEATURES.values():
        for prop, claim in feature.claims.items():
            assert prop in ft.PROPERTIES
            if claim.state == "planned":
                assert claim.owner in tasks, (feature.key, prop)


def test_the_inventory_lists_the_features_and_each_app_claims_its_own():
    snapshot = manifest.snapshot()
    kinds = {
        c["kind"]: {e["id"]: e["manifest"] for e in c["entries"]} for c in snapshot["capabilities"]
    }
    assert set(kinds["feature"]) == set(KEYS)
    assert kinds["feature"]["event"] == "events" and kinds["feature"]["award"] == "awards"
    assert kinds["feature"]["team"] == "participation" and kinds["feature"]["policy"] == "policies"
    assert snapshot["ok"] is True and snapshot["problems"] == []


# --- what the identity verifier catches ---------------------------------------------------------


def test_a_well_formed_independent_feature_passes(isolated):
    """A feature outside the fifteen (a core model) registers with no change to the platform."""
    assert only() == []
    ft.FEATURES["x"] = ft.Feature(
        "x",
        "X",
        "core.SavedView",
        {"identity": identity("field:public_id", "route:saved-view-detail")},
        ft.Lifecycle("none", note="Edited in place and deleted."),
    )
    assert ft.check() == []
    row = next(f for f in ft.report()["features"] if f["key"] == "x")
    assert row["id_type"] == "UUIDField" and row["lifecycle"]["kind"] == "none"


@pytest.mark.parametrize(
    ("over", "code"),
    [
        ({"model": "core.Nope"}, "model_missing"),
        ({"id_field": "nope"}, "id_missing"),
        ({"id_field": "id"}, "id_type"),
        ({"claims": {"identity": ft.provided("route:saved-view-detail")}}, "id_ref"),
        ({"claims": {"identity": ft.provided("field:public_id", "route:nope")}}, "route_missing"),
        ({"claims": {"identity": ft.provided("field:public_id", "route:health")}}, "route_id"),
        (
            {"claims": {"identity": ft.provided("field:public_id", "route:rules-version")}},
            "route_sequential",
        ),
        ({"claims": {"identity": ft.provided("field:public_id", "color:red")}}, "bad_ref"),
        ({"lifecycle": None}, "lifecycle_missing"),
        ({"lifecycle": ft.Lifecycle("none")}, "lifecycle_note"),
        ({"lifecycle": ft.Lifecycle("moon", note="x")}, "lifecycle_kind"),
    ],
)
def test_each_identity_failure_has_a_code(isolated, over, code):
    assert code in codes(only(**over))


def event_life(**over):
    values = {
        "kind": "choice",
        "field": "status",
        "initial": ("draft",),
        "transitions": {"draft": ("open",), "open": ("closed",), "closed": ("archived",)},
        "terminal": ("archived",),
        "via": ("events.views.EventStatusView",),
    }
    values.update(over)
    return ft.Lifecycle(**values)


def event(isolated, **life):
    return only(
        model="events.Event",
        claims={"identity": identity("field:public_id", "route:event-detail")},
        lifecycle=event_life(**life),
    )


def test_a_correct_lifecycle_is_quiet_and_every_wrong_one_is_named(isolated):
    assert event(isolated) == []
    assert "lifecycle_hidden" in codes(
        only(
            model="events.Event",
            claims={"identity": identity("field:public_id")},
            lifecycle=ft.Lifecycle("none", note="x"),
        )
    )
    assert "lifecycle_field" in codes(event(isolated, field="nope"))
    assert "lifecycle_field" in codes(event(isolated, field="name"))  # no choices
    assert "lifecycle_unknown_state" in codes(event(isolated, transitions={"draft": ("limbo",)}))
    assert "lifecycle_unknown_state" in codes(event(isolated, initial=("draft", "ghost")))
    assert "lifecycle_unreachable" in codes(event(isolated, transitions={"draft": ("open",)}))
    assert "lifecycle_terminal" in codes(event(isolated, terminal=("closed",)))
    assert "lifecycle_initial" in codes(
        event(isolated, initial=("open",))
    )  # the model starts at draft
    assert "lifecycle_initial" in codes(event(isolated, initial=()))
    assert "lifecycle_via" in codes(event(isolated, via=("events.views.Nope",)))
    assert "lifecycle_via" in codes(event(isolated, via=()))
    assert "lifecycle_via" in codes(event(isolated, transitions="events.views:NOPE"))


def test_a_timestamp_or_flag_lifecycle_names_its_two_states(isolated):
    flag = ft.Lifecycle(
        "flag",
        field="enabled",
        states=(("off", "Off"), ("on", "On")),
        initial=("on",),
        transitions={"on": ("off",), "off": ("on",)},
        via=("integrations.webhook_views.WebhookSubscriptionView",),
    )
    assert (
        only(
            model="integrations.WebhookSubscription",
            lifecycle=flag,
            claims={"identity": identity("field:public_id", "route:webhook-detail")},
        )
        == []
    )
    wrong_type = ft.Lifecycle(
        "timestamp",
        field="enabled",
        states=(("a", "A"), ("b", "B")),
        initial=("a",),
        transitions={"a": ("b",)},
        via=("integrations.webhook_views.WebhookSubscriptionView",),
    )
    found = only(
        model="integrations.WebhookSubscription",
        lifecycle=wrong_type,
        claims={"identity": identity("field:public_id")},
    )
    assert "lifecycle_field" in codes(found)
    one = ft.Lifecycle(
        "flag", field="enabled", states=(("on", "On"),), initial=("on",), via=("a.b",)
    )
    assert "lifecycle_states" in codes(
        only(
            model="integrations.WebhookSubscription",
            lifecycle=one,
            claims={"identity": identity("field:public_id")},
        )
    )


# --- claims in general --------------------------------------------------------------------------


def test_claims_must_be_well_formed_and_honest(isolated):
    base = {"identity": identity("field:public_id", "route:saved-view-detail")}
    assert "bad_state" in codes(only(claims={**base, "rest": ft.Claim("maybe")}))
    assert "no_refs" in codes(only(claims={**base, "rest": ft.Claim("provided")}))
    assert "no_reason" in codes(only(claims={**base, "rest": ft.Claim("not_applicable")}))
    assert "no_owner" in codes(only(claims={**base, "rest": ft.Claim("planned")}))
    assert "reason_too_long" in codes(only(claims={**base, "rest": ft.not_applicable("x" * 301)}))
    assert "no_verifier" in codes(
        only(claims={**base, "rest": ft.provided("op:get_x")})
    )  # not landed
    assert "unknown_property" in codes(only(claims={**base, "colour": ft.not_applicable("n/a")}))
    assert "unclaimed" in codes(only(claims={}))  # identity is landed, so it must be claimed
    good = only(
        claims={
            **base,
            "rest": ft.planned("PD-F003-B01-T06", "Not yet."),
            "ui_base": ft.not_applicable("Internal."),
        }
    )
    assert good == []


def test_registration_is_idempotent_and_never_silently_replaced(isolated):
    feature = ft.Feature("dup", "Dup", "core.SavedView", {})
    ft.register_feature(feature)
    ft.register_feature(feature)
    with pytest.raises(ValueError):
        ft.register_feature(ft.Feature("dup", "Other", "core.SavedView", {}))
    with pytest.raises(ValueError):
        ft.register_verifier("nope", lambda *a: [])
    with pytest.raises(ValueError):
        ft.register_verifier("identity", lambda *a: [])
    ft.register_verifier("identity", ft.VERIFIERS["identity"])  # the same one again is harmless


# --- the read-only endpoint ---------------------------------------------------------------------


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    foreign = Workspace.objects.create(name="F", slug="f")
    people = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("admin", Role.ADMIN),
        ("par", Role.PARTICIPANT),
        ("judge", Role.JUDGE),
    ):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    stranger = User.objects.create_user(username="stranger", password="unused")
    Membership.objects.create(user=stranger, workspace=foreign, role=Role.ORGANIZER)
    people["stranger"] = stranger
    return {"url": f"/api/v1/workspaces/{workspace.public_id}/completeness/", "people": people}


@pytest.mark.parametrize("who", ["org", "admin"])
def test_organizers_and_admins_read_the_report(world, who):
    response = client_for(world["people"][who]).get(world["url"])
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    body = response.json()
    assert body == json.loads(json.dumps(ft.report()))
    assert body["ok"] is True and len(body["features"]) == 15 and len(body["properties"]) == 21


def test_nobody_else_reads_it_and_nobody_writes_it(world):
    for who in ("par", "judge", "stranger"):
        assert client_for(world["people"][who]).get(world["url"]).status_code == 403, who
    assert Client().get(world["url"]).status_code in (401, 403)
    org = client_for(world["people"]["org"])
    for method in ("post", "put", "patch", "delete"):
        assert getattr(org, method)(world["url"]).status_code == 405


def test_the_endpoint_reports_a_broken_claim_instead_of_hiding_it(world, isolated):
    ft.FEATURES["event"] = ft.Feature(
        "event",
        "Event",
        "events.Event",
        {"identity": identity("field:public_id", "route:nope")},
        ft.FEATURES["event"].lifecycle,
    )
    body = client_for(world["people"]["org"]).get(world["url"]).json()
    assert body["ok"] is False and [p["code"] for p in body["problems"]] == ["route_missing"]
    broken = next(f for f in body["features"] if f["key"] == "event")
    assert [p["code"] for p in broken["problems"]] == ["route_missing"]
