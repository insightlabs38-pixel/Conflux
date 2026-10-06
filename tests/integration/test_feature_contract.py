"""PD-F003-B01-T01: the completeness contract's registry, report and identity verifier."""

import json
import pathlib

import pytest
import yaml
from accounts.models import Session, User
from audit.models import AuditEvent
from core import features as ft
from core import manifest
from django.core.exceptions import ValidationError
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


VALID = ft.provided(
    "check:core.saved_views.validate_name",
    "constraint:core.SavedView.unique_saved_view_name",
    "test:tests/integration/test_saved_views.py::test_defaults_and_validation_happen_at_save_time",
)

AUTHZ = ft.provided(
    "route:saved-view-list",
    "route:saved-view-detail",
    "scope:event",
    "readers:members",
    "writers:members",
    "own:self",
    "test:tests/integration/test_saved_views.py::test_private_views_belong_to_the_owner_and_organizers_views_are_shared_for_reading",
)


def identity(*refs):
    return ft.provided(*(refs or ("field:public_id",)))


def only(feature_key="x", **over):
    """A registry holding one feature on a real model, ready to be made wrong."""
    values = {
        "key": feature_key,
        "label": "X",
        "model": "core.SavedView",
        "claims": {
            "identity": identity("field:public_id", "route:saved-view-detail"),
            "validation": VALID,
            "authorization": AUTHZ,
        },
        "lifecycle": ft.Lifecycle("none", note="Edited in place."),
    }
    values.update(over)
    values["claims"] = {"validation": VALID, "authorization": AUTHZ, **values["claims"]}
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature(**values))
    # every other landed property must be claimed for the registry to be quiet about it
    return ft.check()


# --- the real system ----------------------------------------------------------------------------


def test_the_fifteen_features_agree_with_the_live_system():
    assert sorted(ft.FEATURES) == KEYS
    assert ft.check() == []
    assert ft.landed() == ["identity", "validation", "authorization"]


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
        {
            "identity": identity("field:public_id", "route:saved-view-detail"),
            "validation": VALID,
            "authorization": AUTHZ,
        },
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
        {
            "identity": identity("field:public_id", "route:nope"),
            "validation": ft.FEATURES["event"].claims["validation"],
            "authorization": ft.FEATURES["event"].claims["authorization"],
        },
        ft.FEATURES["event"].lifecycle,
    )
    body = client_for(world["people"]["org"]).get(world["url"]).json()
    assert body["ok"] is False and [p["code"] for p in body["problems"]] == ["route_missing"]
    broken = next(f for f in body["features"] if f["key"] == "event")
    assert [p["code"] for p in broken["problems"]] == ["route_missing"]


# --- the validation verifier (T02) --------------------------------------------------------------


class Blank:
    """A model-like stand-in that behaves as told, for the probes a real model never fails."""

    class _meta:
        constraints = ()

    def __init__(self, fields=None, full=None):
        self._fields, self._full = fields, full

    def clean_fields(self):
        if isinstance(self._fields, Exception):
            raise self._fields
        if self._fields:
            raise ValidationError({name: ["Required."] for name in self._fields})

    def full_clean(self, **kwargs):
        if self._full:
            raise self._full


class Probe(ft.System):
    def __init__(self, behaviour):
        super().__init__()
        self.behaviour = behaviour

    def model(self, label):
        if label == "stub.Blank":
            behaviour = self.behaviour
            return type("Stub", (Blank,), {"__init__": lambda me: Blank.__init__(me, *behaviour)})
        return super().model(label)


def verify_validation(refs, behaviour=(["name"], None)):
    feature = ft.Feature("s", "S", "stub.Blank", {"validation": ft.provided(*refs)})
    return ft.VERIFIERS["validation"](feature, feature.claims["validation"], Probe(behaviour))


GOOD = ("check:core.saved_views.validate_name", "test:tests/integration/test_x.py::test_y")


def test_a_real_claim_is_enforced_proved_and_derived_from_the_model():
    assert ft.check() == [] and ft.check_static(ROOT) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["submission"]["facts"]["validation"]["blank_refused"] == [
        "project",
        "stage",
        "updated_by",
    ]
    assert row["event"]["facts"]["validation"] == {
        "blank_refused": ["name", "slug", "workspace"],
        "constraints": ["unique_event_slug_workspace"],
        "own_clean": True,
    }
    for feature in ft.FEATURES.values():
        kinds = {r.partition(":")[0] for r in feature.claims["validation"].refs}
        assert "test" in kinds and kinds & {"check", "constraint"}, feature.key


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (("color:red",) + GOOD, "bad_ref"),
        (("check:core.saved_views.nope",) + GOOD, "check_missing"),
        (("constraint:core.SavedView.nope",) + GOOD, "constraint_missing"),
        (("constraint:core.Nope.x",) + GOOD, "constraint_missing"),
        (("test:somewhere/test_x.py::test_y",) + GOOD, "test_ref"),
        (("test:tests/integration/test_x.py::test_y",), "no_enforcement"),
        (("check:core.saved_views.validate_name",), "no_test"),
    ],
)
def test_each_validation_ref_failure_has_a_code(refs, code):
    assert code in codes(verify_validation(refs))


def test_the_blank_probe_catches_a_model_that_accepts_or_crashes_on_a_blank_record():
    assert verify_validation(GOOD) == []
    assert "blank_accepted" in codes(verify_validation(GOOD, ([], None)))
    assert "blank_error" in codes(verify_validation(GOOD, (RuntimeError("boom"), None)))
    assert "blank_crashes" in codes(verify_validation(GOOD, (["name"], KeyError("stage"))))
    assert codes(verify_validation(GOOD, (["name"], ValidationError("keyed")))) == []


def test_the_ci_check_finds_a_missing_test_file_or_name(isolated, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_there.py").write_text("def test_present():\n    pass\n")
    claim = ft.provided(
        "check:core.saved_views.validate_name",
        "test:tests/test_there.py::test_present",
        "test:tests/test_there.py::test_absent",
        "test:tests/test_gone.py::test_anything",
    )
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", {"validation": claim}))
    assert codes(ft.check_static(tmp_path)) == ["test_file", "test_name"]


# --- authorization (T03) --------------------------------------------------------------------------


def verify_authorization(refs, model="core.SavedView"):
    feature = ft.Feature("s", "S", model, {"authorization": ft.provided(*refs)})
    return ft.VERIFIERS["authorization"](feature, feature.claims["authorization"], ft.System())


def swap(old, new):
    return tuple(new if r == old else r for r in AUTHZ.refs if new or r != old)


def test_a_real_authorization_claim_is_derived_from_the_permission_matrix():
    assert verify_authorization(AUTHZ.refs) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["track"]["facts"]["authorization"]
    assert (facts["readers"], facts["writers"]) == ("members", "admin,organizer")
    assert facts["scope_path"] == ["Track", "Event"]
    assert facts["explanation"]["outcome"] == "allowed"
    assert facts["explanation"]["summary"].startswith("Read: members. Change: admin,organizer.")
    for feature in ft.FEATURES.values():
        refs = {r.partition(":")[0] for r in feature.claims["authorization"].refs}
        assert {"route", "scope", "readers", "writers", "test"} <= refs, feature.key


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (swap("readers:members", "readers:admin,organizer"), "readers_mismatch"),
        (swap("writers:members", "writers:admin,organizer"), "writers_mismatch"),
        (swap("readers:members", "readers:none"), "readers_mismatch"),
        (swap("own:self", ""), "own_missing"),
        (swap("own:self", "own:anybody"), "own_ref"),
        (swap("scope:event", ""), "scope_ref"),
        (swap("scope:event", "scope:planet"), "scope_ref"),
        (swap("route:saved-view-detail", "route:nope"), "route_missing"),
        (swap("route:saved-view-detail", "route:accounts-me"), "route_tenant"),
        (swap("route:saved-view-detail", "route:public-event-state"), "route_open"),
        (tuple(r for r in AUTHZ.refs if not r.startswith("route:")), "no_routes"),
        (tuple(r for r in AUTHZ.refs if not r.startswith("test:")), "no_test"),
        (swap("scope:event", "color:red"), "bad_ref"),
    ],
)
def test_each_authorization_failure_has_a_code(refs, code):
    found = codes(verify_authorization(refs))
    assert code in found


def test_an_open_route_must_be_acknowledged_and_organizer_only_writes_declare_no_object_rule():
    refs = swap("route:saved-view-detail", "route:public-event-state")
    assert "route_open" in codes(verify_authorization(refs))
    assert "route_open" not in codes(verify_authorization((*refs, "open:public-event-state")))
    only_organizers = (
        "route:track-list",
        "scope:event",
        "readers:members",
        "writers:admin,organizer",
        "test:tests/x.py::test_y",
    )
    assert verify_authorization(only_organizers, "events.Track") == []
    assert "own_unused" in codes(
        verify_authorization((*only_organizers, "own:self"), "events.Track")
    )


def test_a_model_with_no_chain_to_its_scope_is_refused():
    refs = swap("scope:event", "scope:event")
    assert "scope_path" in codes(verify_authorization(refs, "accounts.User"))


def test_the_authorization_ci_check_finds_a_missing_test(isolated, tmp_path):
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", {"authorization": AUTHZ}))
    assert codes(ft.check_static(tmp_path)) == ["test_file"]
