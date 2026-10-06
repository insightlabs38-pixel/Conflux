"""PD-F003-B01-T01: the completeness contract's registry, report and identity verifier."""

import json
import pathlib
import re

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

AUDIT = ft.provided(
    "write:saved-view-list:POST=saved_view.created",
    "write:saved-view-detail:PATCH=saved_view.updated",
    "write:saved-view-detail:DELETE=saved_view.deleted",
    "test:tests/integration/test_saved_views.py::test_deleting_a_view_is_audited_and_leaves_the_data",
)

IDEM = ft.provided(
    "mode:saved-view-list:POST=unique@core.SavedView.unique_saved_view_name",
    "mode:saved-view-detail:PATCH=locked@core.SavedView.version",
    "mode:saved-view-detail:DELETE=natural",
    "test:tests/integration/test_saved_views.py::test_updates_bump_the_version_refuse_stale_writers_and_are_audited_without_filter_values",
)

REST = ft.provided(
    "list:saved-view-list",
    "detail:saved-view-detail",
    "paging:unpaged@bounded: a person saves a few views per event and entity",
    "test:tests/integration/test_saved_views.py::test_views_are_scoped_to_their_event_and_workspace_and_deleted_with_it",
)

SDKC = ft.provided(
    "generated:python",
    "generated:typescript",
    "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
)

SEARCH = ft.provided("no_query@read whole through its list: a person saves a few views per event")

UI = ft.provided("no_ui@a saved view is made from the grid toolbar, not on a screen of its own")

ADV = ft.provided("no_advanced@nothing sits beyond the base screen of a saved view in this test")

BULK = ft.provided("no_bulk@a saved view belongs to one person and is never changed in a batch")


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
            "audit": AUDIT,
            "idempotency": IDEM,
            "rest": REST,
            "sdk": SDKC,
            "search": SEARCH,
            "ui_base": UI,
            "ui_advanced": ADV,
            "bulk": BULK,
        },
        "lifecycle": ft.Lifecycle("none", note="Edited in place."),
    }
    values.update(over)
    values["claims"] = {
        "validation": VALID,
        "authorization": AUTHZ,
        "audit": AUDIT,
        "idempotency": IDEM,
        "rest": REST,
        "sdk": SDKC,
        "search": SEARCH,
        "ui_base": UI,
        "ui_advanced": ADV,
        "bulk": BULK,
        **values["claims"],
    }
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature(**values))
    # every other landed property must be claimed for the registry to be quiet about it
    return ft.check()


# --- the real system ----------------------------------------------------------------------------


def test_the_fifteen_features_agree_with_the_live_system():
    assert sorted(ft.FEATURES) == KEYS
    assert ft.check() == []
    assert ft.landed() == [
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
    ]


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
    assert first["totals"]["fixtures"]["unclaimed"] == 15  # not landed yet, so only unclaimed
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
            "audit": AUDIT,
            "idempotency": IDEM,
            "rest": REST,
            "sdk": SDKC,
            "search": SEARCH,
            "ui_base": UI,
            "ui_advanced": ADV,
            "bulk": BULK,
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
    assert "bad_state" in codes(only(claims={**base, "fixtures": ft.Claim("maybe")}))
    assert "no_refs" in codes(only(claims={**base, "fixtures": ft.Claim("provided")}))
    assert "no_reason" in codes(only(claims={**base, "fixtures": ft.Claim("not_applicable")}))
    assert "no_owner" in codes(only(claims={**base, "fixtures": ft.Claim("planned")}))
    assert "reason_too_long" in codes(
        only(claims={**base, "fixtures": ft.not_applicable("x" * 301)})
    )
    assert "no_verifier" in codes(
        only(claims={**base, "fixtures": ft.provided("op:get_x")})
    )  # not landed
    assert "unknown_property" in codes(only(claims={**base, "colour": ft.not_applicable("n/a")}))
    assert "unclaimed" in codes(only(claims={}))  # identity is landed, so it must be claimed
    good = only(
        claims={
            **base,
            "fixtures": ft.planned("PD-F003-B03-T01", "Not yet."),
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
            "audit": ft.FEATURES["event"].claims["audit"],
            "idempotency": ft.FEATURES["event"].claims["idempotency"],
            "rest": ft.FEATURES["event"].claims["rest"],
            "sdk": ft.FEATURES["event"].claims["sdk"],
            "search": ft.FEATURES["event"].claims["search"],
            "ui_base": ft.FEATURES["event"].claims["ui_base"],
            "ui_advanced": ft.FEATURES["event"].claims["ui_advanced"],
            "bulk": ft.FEATURES["event"].claims["bulk"],
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
        (AUTHZ.refs + ("narrow:saved-view-detail:GET=none",), "narrow_unused"),
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


# --- audit (T04) ----------------------------------------------------------------------------------


def verify_audit(refs, model="core.SavedView", authorization=AUTHZ):
    claims = {"audit": ft.provided(*refs)}
    if authorization is not None:
        claims["authorization"] = authorization
    feature = ft.Feature("s", "S", model, claims)
    return ft.VERIFIERS["audit"](feature, feature.claims["audit"], ft.System())


def without(*drop):
    return tuple(r for r in AUDIT.refs if r not in drop)


def test_a_real_audit_claim_is_derived_from_the_code():
    assert verify_audit(AUDIT.refs) == []
    actions = ft.System().audit_actions()
    assert actions["saved_view.created"] == ("core",)
    assert actions["track.created"] == ("events",)  # recorded through a helper's action=
    assert actions["announcement.reviewed"] == ("communications",)  # assigned to a name first
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["track"]["facts"]["audit"]
    assert facts["changes"] == [
        "POST track-list: track.created",
        "PATCH track-detail: track.updated",
        "DELETE track-detail: track.deleted",
    ]
    assert facts["actions"] == ["track.created", "track.deleted", "track.updated"]
    for feature in ft.FEATURES.values():
        kinds = {r.partition(":")[0] for r in feature.claims["audit"].refs}
        assert kinds == {"write", "test"}, feature.key
        # every action follows subject.verb and is recorded by the code
        for ref in feature.claims["audit"].refs:
            if ref.startswith("write:"):
                assert ft.AUDIT_ACTION.fullmatch(ref.rpartition("=")[2])


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (without("write:saved-view-detail:DELETE=saved_view.deleted"), "write_unaudited"),
        (
            without("write:saved-view-list:POST=saved_view.created")
            + ("write:saved-view-list:POST=saved_view.nope",),
            "action_missing",
        ),
        (
            without("write:saved-view-list:POST=saved_view.created")
            + ("write:saved-view-list:POST=Saved.View",),
            "action_format",
        ),
        (
            without("write:saved-view-list:POST=saved_view.created")
            + ("write:saved-view-list:POST=track.created",),
            "action_elsewhere",
        ),
        (AUDIT.refs + ("write:saved-view-list:POST=saved_view.created",), "write_twice"),
        (AUDIT.refs + ("write:nope:POST=saved_view.created",), "route_missing"),
        (AUDIT.refs + ("write:saved-view-list:PUT=saved_view.created",), "method_unknown"),
        (AUDIT.refs + ("write:saved-view-list=saved_view.created",), "bad_ref"),
        (AUDIT.refs + ("color:red",), "bad_ref"),
        (tuple(r for r in AUDIT.refs if not r.startswith("test:")), "no_test"),
        (tuple(r for r in AUDIT.refs if not r.startswith("write:")), "no_writes"),
    ],
)
def test_each_audit_failure_has_a_code(refs, code):
    assert code in codes(verify_audit(refs))


def test_a_route_that_only_reads_cannot_be_claimed_as_a_change():
    refs = AUDIT.refs + ("write:accounts-me:GET=saved_view.created",)
    assert "bad_ref" in codes(verify_audit(refs))


def test_completeness_is_derived_from_the_authorization_claim_only_when_there_is_one():
    # no authorization claim: nothing to derive the changes from, so only the refs are checked
    assert (
        verify_audit(
            without("write:saved-view-detail:DELETE=saved_view.deleted"), authorization=None
        )
        == []
    )


def test_the_audit_ci_check_finds_a_missing_test(isolated, tmp_path):
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", {"audit": AUDIT}))
    assert codes(ft.check_static(tmp_path)) == ["test_file"]


# --- idempotency (T05) ----------------------------------------------------------------------------


def verify_idempotency(refs, model="core.SavedView", authorization=AUTHZ):
    claims = {"idempotency": ft.provided(*refs)}
    if authorization is not None:
        claims["authorization"] = authorization
    feature = ft.Feature("s", "S", model, claims)
    return ft.VERIFIERS["idempotency"](feature, feature.claims["idempotency"], ft.System())


def mode_swap(old, new):
    return tuple(new if r == old else r for r in IDEM.refs)


def test_a_real_idempotency_claim_is_derived_from_the_system():
    assert verify_idempotency(IDEM.refs) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["track"]["facts"]["idempotency"]
    assert facts["repeats"] == [
        "POST track-list: unique (events.Track.unique_track_name_event)",
        "PATCH track-detail: natural",
        "DELETE track-detail: natural",
    ]
    assert facts["modes"] == ["natural", "unique"]
    assert "keyed" in row["message"]["facts"]["idempotency"]["modes"]
    assert ft.System().view_class("message-list-create") is not None
    for feature in ft.FEATURES.values():
        kinds = {r.partition(":")[0] for r in feature.claims["idempotency"].refs}
        assert kinds == {"mode", "test"}, feature.key


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (
            mode_swap(
                "mode:saved-view-list:POST=unique@core.SavedView.unique_saved_view_name",
                "mode:saved-view-list:POST=unique@core.SavedView.nope",
            ),
            "unique_missing",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:DELETE=natural", "mode:saved-view-detail:DELETE=magic"
            ),
            "mode_unknown",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:DELETE=natural", "mode:saved-view-detail:DELETE=natural@why"
            ),
            "mode_detail",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:DELETE=natural",
                "mode:saved-view-detail:DELETE=token@core.SavedView.name",
            ),
            "token_missing",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:DELETE=natural",
                "mode:saved-view-detail:DELETE=token@core.SavedView.public_id",
            ),
            None,
        ),
        (
            mode_swap(
                "mode:saved-view-detail:PATCH=locked@core.SavedView.version",
                "mode:saved-view-detail:PATCH=locked@core.SavedView.nope",
            ),
            "lock_missing",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:PATCH=locked@core.SavedView.version",
                "mode:saved-view-detail:PATCH=locked@core.saved_views.validate_name",
            ),
            "lock_missing",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:DELETE=natural", "mode:saved-view-detail:DELETE=keyed"
            ),
            "not_keyed",
        ),
        (
            mode_swap(
                "mode:saved-view-detail:DELETE=natural", "mode:saved-view-detail:DELETE=none@short"
            ),
            "no_reason",
        ),
        (tuple(r for r in IDEM.refs if "DELETE" not in r), "mode_missing"),
        (IDEM.refs + ("mode:saved-view-detail:DELETE=natural",), "mode_twice"),
        (IDEM.refs + ("mode:nope:POST=natural",), "route_missing"),
        (IDEM.refs + ("mode:saved-view-list:PUT=natural",), "method_unknown"),
        (IDEM.refs + ("mode:saved-view-list=natural",), "bad_ref"),
        (IDEM.refs + ("color:red",), "bad_ref"),
        (tuple(r for r in IDEM.refs if not r.startswith("test:")), "no_test"),
        (tuple(r for r in IDEM.refs if not r.startswith("mode:")), "no_modes"),
    ],
)
def test_each_idempotency_failure_has_a_code(refs, code):
    found = codes(verify_idempotency(refs))
    assert (code in found) if code else found == []


def test_a_lock_is_found_in_code_that_really_takes_one_and_a_key_in_a_view_that_takes_it():
    system = ft.System()
    ok = "mode:saved-view-detail:PATCH=locked@events.registration.decide_application"
    refs = mode_swap("mode:saved-view-detail:PATCH=locked@core.SavedView.version", ok)
    assert verify_idempotency(refs) == []
    keyed = mode_swap(
        "mode:saved-view-list:POST=unique@core.SavedView.unique_saved_view_name",
        "mode:saved-view-list:POST=keyed",
    )
    assert "not_keyed" in codes(verify_idempotency(keyed))
    assert issubclass(
        system.view_class("project-list"),
        __import__("core.idempotency", fromlist=["x"]).IdempotentMixin,
    )


def test_the_idempotency_ci_check_finds_a_missing_test(isolated, tmp_path):
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", {"idempotency": IDEM}))
    assert codes(ft.check_static(tmp_path)) == ["test_file"]


# --- REST representation (T06) --------------------------------------------------------------------


def verify_rest(refs, model="core.SavedView", authorization=AUTHZ):
    claims = {"rest": ft.provided(*refs)}
    if authorization is not None:
        claims["authorization"] = authorization
    feature = ft.Feature("s", "S", model, claims)
    return ft.VERIFIERS["rest"](feature, feature.claims["rest"], ft.System())


def rest_swap(old, new):
    return tuple(new if r == old else r for r in REST.refs)


def test_a_real_rest_claim_is_derived_from_the_openapi_document():
    assert verify_rest(REST.refs) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["track"]["facts"]["rest"]
    assert facts["lists"] == ["GET track-list: array of Track"]
    assert facts["paging"] == "unpaged" and "no_detail" in facts
    assert row["message"]["facts"]["rest"]["paging"] == "offset"
    assert row["submission"]["facts"]["rest"]["detail"] == "GET submission-detail: SubmissionSchema"
    for feature in ft.FEATURES.values():
        kinds = {r.partition(":")[0].partition("@")[0] for r in feature.claims["rest"].refs}
        assert {"paging", "test"} <= kinds, feature.key
        assert ("list" in kinds) != ("no_list" in kinds)
        assert ("detail" in kinds) != ("no_detail" in kinds)


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (rest_swap("list:saved-view-list", "list:nope"), "route_missing"),
        (rest_swap("list:saved-view-list", "list:saved-view-detail"), "list_shape"),
        (rest_swap("detail:saved-view-detail", "detail:saved-view-list"), "detail_shape"),
        (rest_swap("detail:saved-view-detail", "detail:accounts-login"), "detail_missing"),
        (rest_swap("list:saved-view-list", "list:accounts-login"), "list_missing"),
        (
            rest_swap(
                "paging:unpaged@bounded: a person saves a few views per event and entity",
                "paging:offset",
            ),
            "paging_mismatch",
        ),
        (
            rest_swap(
                "paging:unpaged@bounded: a person saves a few views per event and entity",
                "paging:unpaged@short",
            ),
            "no_reason",
        ),
        (
            rest_swap(
                "paging:unpaged@bounded: a person saves a few views per event and entity",
                "paging:forever",
            ),
            "paging_ref",
        ),
        (tuple(r for r in REST.refs if not r.startswith("paging")), "paging_ref"),
        (rest_swap("detail:saved-view-detail", "no_detail@short"), "no_reason"),
        (REST.refs + ("no_list@a feature with a list cannot also say it has none",), "list_both"),
        (tuple(r for r in REST.refs if not r.startswith("detail")), "detail_ref"),
        (REST.refs + ("detail:saved-view-detail",), "detail_twice"),
        (REST.refs + ("color:red",), "bad_ref"),
        (tuple(r for r in REST.refs if not r.startswith("test:")), "no_test"),
    ],
)
def test_each_rest_failure_has_a_code(refs, code):
    assert code in codes(verify_rest(refs))


def test_a_feature_without_a_list_says_so_and_has_nothing_to_page():
    refs = (
        "no_list@a person has one of these per event and reads it directly",
        "detail:saved-view-detail",
        "test:tests/x.py::test_y",
    )
    assert verify_rest(refs) == []
    assert "paging_unused" in codes(verify_rest((*refs, "paging:offset")))


def test_a_writing_route_the_document_does_not_describe_is_reported(monkeypatch):
    class Gap(ft.System):
        def operation(self, route, method):
            return (
                None
                if (route, method) == ("saved-view-list", "POST")
                else super().operation(route, method)
            )

    feature = ft.Feature("s", "S", "core.SavedView", {"rest": REST, "authorization": AUTHZ})
    found = ft.VERIFIERS["rest"](feature, REST, Gap())
    assert "op_missing" in codes(found)


def test_the_rest_ci_check_finds_a_missing_test(isolated, tmp_path):
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", {"rest": REST}))
    assert codes(ft.check_static(tmp_path)) == ["test_file"]


# --- generated SDK (T07) --------------------------------------------------------------------------


def verify_sdk(refs, authorization=AUTHZ, model="core.SavedView"):
    claims = {"sdk": ft.provided(*refs)}
    if authorization is not None:
        claims["authorization"] = authorization
    feature = ft.Feature("s", "S", model, claims)
    return ft.VERIFIERS["sdk"](feature, feature.claims["sdk"], ft.System())


def test_a_real_sdk_claim_derives_each_operation_and_its_typescript_type():
    assert verify_sdk(SDKC.refs) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["track"]["facts"]["sdk"]
    assert "GET track-list: Track[]" in facts["operations"]
    assert "POST track-list: Track" in facts["operations"]
    assert "DELETE track-detail: null" in facts["operations"]
    assert facts["count"] == len(facts["operations"]) == 4
    assert ft.check_static(ROOT) == []


@pytest.mark.parametrize(
    ("refs", "authorization", "code"),
    [
        (("generated:python", "test:tests/x.py::test_y"), AUTHZ, "target_missing"),
        (SDKC.refs + ("generated:go",), AUTHZ, "bad_target"),
        (SDKC.refs + ("color:red",), AUTHZ, "bad_ref"),
        (tuple(r for r in SDKC.refs if r.startswith("generated")), AUTHZ, "no_test"),
        (SDKC.refs, None, "no_operations"),
    ],
)
def test_each_sdk_failure_has_a_code(refs, authorization, code):
    assert code in codes(verify_sdk(refs, authorization))


def test_an_operation_missing_from_the_document_or_duplicated_is_reported(monkeypatch):
    class Gap(ft.System):
        def operation(self, route, method):
            if (route, method) == ("saved-view-list", "POST"):
                return None
            return super().operation(route, method)

    feature = ft.Feature("s", "S", "core.SavedView", {"sdk": SDKC, "authorization": AUTHZ})
    assert "op_missing" in codes(ft.VERIFIERS["sdk"](feature, SDKC, Gap()))

    class Twice(ft.System):
        def openapi(self):
            document = super().openapi()
            return {
                "paths": {
                    **document["paths"],
                    "/dup/": {"get": {"operationId": "dup"}},
                    "/dup2/": {"get": {"operationId": "dup"}},
                }
            }

        def operation(self, route, method):
            return (
                {"operationId": "dup"}
                if (route, method) == ("saved-view-list", "GET")
                else super().operation(route, method)
            )

    found = ft.VERIFIERS["sdk"](feature, SDKC, Twice())
    assert "op_id_twice" in codes(found)


def sdk_tree(tmp_path, *, ts_type="SavedViewSchema[]", python=True, ts=True):
    """A copy of the two generated files with one operation changed, to prove the CI check."""
    system = ft.System()
    op = system.operation("saved-view-list", "GET")["operationId"]
    (tmp_path / "tests/integration").mkdir(parents=True)
    (tmp_path / "tests/integration/test_feature_sdk.py").write_text(
        "def test_every_claimed_operation_works_through_the_generated_python_sdk():\n    pass\n"
    )
    (tmp_path / "tests/integration/test_saved_views.py").write_text("")
    (tmp_path / "sdks/python/conflux_sdk").mkdir(parents=True)
    (tmp_path / "sdks/typescript").mkdir(parents=True)
    py = (ROOT / "sdks/python/conflux_sdk/generated.py").read_text()
    ts_text = (ROOT / "sdks/typescript/generated.ts").read_text()
    if not python:
        py = py.replace(f"'{op}': {{'method'", f"'x{op}': {{'method'")
    if not ts:
        ts_text = ts_text.replace(f"  {op}: {{\n    method:", f"  x{op}: {{\n    method:")
    block = re.search(rf"^  {op}:\s*\{{\s*request:(.*?)^  \}};", ts_text, flags=re.S | re.M)
    ts_text = ts_text.replace(
        block.group(0),
        block.group(0).replace("response: SavedViewSchema[];", f"response: {ts_type};"),
    )
    (tmp_path / "sdks/python/conflux_sdk/generated.py").write_text(py)
    (tmp_path / "sdks/typescript/generated.ts").write_text(ts_text)


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, []),
        ({"python": False}, ["python_missing"]),
        ({"ts": False}, ["ts_missing"]),
        ({"ts_type": "SavedViewSchema"}, ["ts_type_mismatch"]),
    ],
)
def test_the_sdk_ci_check_compares_the_generated_files_with_openapi(
    isolated, tmp_path, options, expected
):
    sdk_tree(tmp_path, **options)
    claims = {
        "authorization": ft.provided(
            "route:saved-view-list",
            "scope:event",
            "readers:members",
            "writers:members",
            "own:self",
            "test:tests/integration/test_saved_views.py::test_x",
        ),  # fmt: skip
        "sdk": SDKC,
    }
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", claims))
    found = [p for p in ft.check_static(tmp_path) if p["property"] == "sdk"]
    assert sorted(set(codes(found)) - {"test_name"}) == expected


def test_the_sdk_ci_check_reports_a_tree_without_the_generated_files(isolated, tmp_path):
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "core.SavedView", {"sdk": SDKC}))
    assert "sdk_missing" in codes(ft.check_static(tmp_path))


# --- search (T08) ---------------------------------------------------------------------------------

APPLICATION_FIELDS = "username,status,note,waitlist_position,decided_by,decided_at,created_at"
ENTITY = (
    "entity:applications",
    f"fields:{APPLICATION_FIELDS}",
    "test:tests/integration/test_entity_query.py::test_every_registered_field_resolves_against_the_database",
)


def verify_search(refs, model="events.EventApplication", authorization=None):
    claims = {"search": ft.provided(*refs)}
    if authorization is not None:
        claims["authorization"] = authorization
    feature = ft.Feature("s", "S", model, claims)
    return ft.VERIFIERS["search"](feature, feature.claims["search"], ft.System())


def test_a_real_search_claim_is_derived_from_the_registry_and_the_model():
    assert verify_search(ENTITY) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["application"]["facts"]["search"]
    assert facts["query"] == "entity applications" and facts["roles"] == ["admin", "organizer"]
    assert "username (text, filter, sort, indexed)" in facts["fields"]
    assert "status (enum, filter, sort, scan within one event)" in facts["fields"]
    assert row["track"]["facts"]["search"]["query"] == "not offered"
    entities = {
        f["key"] for f in ft.report()["features"] if f["facts"]["search"]["query"] != "not offered"
    }
    assert entities == {"application", "project"}


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (("entity:nope", f"fields:{APPLICATION_FIELDS}", ENTITY[2]), "entity_missing"),
        (("entity:applications", "fields:username,status", ENTITY[2]), "fields_mismatch"),
        (
            ("entity:applications", f"fields:{APPLICATION_FIELDS},extra", ENTITY[2]),
            "fields_mismatch",
        ),
        (("entity:applications", ENTITY[2]), "fields_ref"),
        (ENTITY[:2], "no_test"),
        (("fields:username", ENTITY[2]), "entity_ref"),
        (ENTITY + ("no_query@a feature cannot be an entity and say it is not",), "both"),
        (("no_query@short",), "no_reason"),
        (ENTITY + ("color:red",), "bad_ref"),
    ],
)
def test_each_search_failure_has_a_code(refs, code):
    assert code in codes(verify_search(refs))


def test_a_column_the_model_does_not_have_and_one_with_no_event_to_narrow_by_are_refused():
    from core import entities as registry

    broken = registry.Entity(
        key="people",
        label="People",
        roles=("admin",),
        base=lambda event, user: None,
        fields=(
            registry.Field("name", registry.TEXT, "no_such_column", "Name"),
            registry.Field("joined", registry.DATE, "date_joined", "Joined"),
        ),
    )
    registry._ENTITIES["people"] = broken
    try:
        found = codes(verify_search(
            ("entity:people", "fields:name,joined", ENTITY[2]), model="accounts.User"
        ))  # fmt: skip
    finally:
        del registry._ENTITIES["people"]
    assert "column_unresolved" in found and "unindexed_filter" in found


def test_an_entity_may_not_let_a_role_search_what_the_routes_refuse_it():
    organizers_only = ft.provided(
        "route:event-application-list", "scope:event", "readers:organizer", "writers:organizer",
        "test:tests/x.py::test_y",
    )  # fmt: skip
    assert verify_search(ENTITY, authorization=organizers_only) != []
    assert "roles_wider" in codes(verify_search(ENTITY, authorization=organizers_only))
    both = ft.provided(
        "route:event-application-list", "scope:event", "readers:admin,organizer",
        "writers:admin,organizer", "test:tests/x.py::test_y",
    )  # fmt: skip
    assert "roles_wider" not in codes(verify_search(ENTITY, authorization=both))


def test_a_no_query_claim_needs_a_reason_and_the_search_ci_check_finds_a_missing_test(
    isolated, tmp_path
):
    assert verify_search(("no_query@read whole through its list: a handful of rows",)) == []
    ft.FEATURES.clear()
    ft.register_feature(
        ft.Feature("x", "X", "events.EventApplication", {"search": ft.provided(*ENTITY)})
    )
    assert codes(ft.check_static(tmp_path)) == ["test_file"]


def test_the_audit_action_scan_follows_helpers_and_ignores_other_action_keywords():
    import ast
    import textwrap

    tree = ast.parse(
        textwrap.dedent(
            """
            def _audit(actor, thing, *, action, **extra):
                record_mutation(actor=actor, action=action, target=thing)

            def _not_audit(actor, *, action):
                log(action)

            def _renames(actor, *, kind):
                record_mutation(actor=actor, action="fixed.verb")
            """
        )
    )
    from core.features import _helper_names

    assert _helper_names([tree]) == {"_audit"}  # only a function that hands `action` on
    actions = ft.System().audit_actions()
    assert "track.created" in actions and "team.invite_redeemed" in actions
    assert "x.y" not in actions and all(ft.AUDIT_ACTION.fullmatch(a) for a in actions)


def only_mentions_a_lock():
    """Does not call select_for_update, only says it."""
    return "select_for_update"  # select_for_update


def really_takes_a_lock():
    return ft.System().model("core.SavedView").objects.select_for_update()


def test_a_lock_must_be_a_call_and_a_version_must_be_a_version_and_a_key_must_cover_the_method():
    here = "tests.integration.test_feature_contract"
    detail = "mode:saved-view-detail:PATCH=locked@"
    assert verify_idempotency(mode_swap(IDEM.refs[1], f"{detail}{here}.really_takes_a_lock")) == []
    for wrong in (f"{here}.only_mentions_a_lock", "core.SavedView.name"):
        found = verify_idempotency(mode_swap(IDEM.refs[1], f"{detail}{wrong}"))
        assert "lock_missing" in codes(found), wrong
    from core import features_idempotency as fi

    system = ft.System()
    assert fi._keyed(system, "project-list", "POST")
    assert not fi._keyed(system, "project-list", "DELETE")  # the mixin only keys POST, PUT, PATCH


def test_a_route_narrower_than_the_claim_is_pinned_so_widening_it_alone_fails():
    refs = (
        "route:submission-detail",
        "route:submission-reopen",
        "scope:event",
        "readers:members",
        "writers:members",
        "own:project_member",
        "test:tests/x.py::test_y",
    )
    found = codes(verify_authorization(refs, "projects.Submission"))
    assert "narrow_missing" in found  # reopen is organizers only, the claim says members
    pinned = (*refs, "narrow:submission-reopen:POST=admin,organizer")
    assert verify_authorization(pinned, "projects.Submission") == []
    wrong = (*refs, "narrow:submission-reopen:POST=members")
    assert "narrow_mismatch" in codes(verify_authorization(wrong, "projects.Submission"))
    real = ft.FEATURES["submission"].claims["authorization"].refs
    assert "narrow:submission-reopen:POST=admin,organizer" in real


# --- base UI (T01) --------------------------------------------------------------------------------

SCREEN = (
    "component:src/web/features/tracks/TrackPanel.tsx",
    "test:src/web/features/tracks/TrackPanel.test.tsx",
)


def verify_ui_base(refs, authorization=AUTHZ):
    claims = {"ui_base": ft.provided(*refs)}
    if authorization is not None:
        claims["authorization"] = authorization
    feature = ft.Feature("s", "S", "core.SavedView", claims)
    return ft.VERIFIERS["ui_base"](feature, feature.claims["ui_base"], ft.System())


def test_a_real_ui_base_claim_names_a_screen_a_test_and_what_it_reads():
    assert verify_ui_base(SCREEN) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["track"]["facts"]["ui_base"]
    assert facts["screens"] == ["EventDashboard.tsx"] and facts["tests"] == [
        "EventDashboard.test.tsx"
    ]
    assert facts["reads"] == ["tracks"]
    assert row["event"]["facts"]["ui_base"]["screens"] == ["EventDashboard.tsx", "CreateEvent.tsx"]
    assert row["announcement"]["claims"]["ui_base"]["state"] == "planned"
    assert row["announcement"]["claims"]["ui_base"]["owner"] == "PD-S009-B02-T03"


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (("no_ui@short",), "no_reason"),
        (SCREEN + ("no_ui@a long enough reason why there is no screen at all",), "both"),
        (SCREEN[:1], "no_test"),
        (SCREEN[1:], "no_component"),
        (("component:src/web/features/x/Y.ts", SCREEN[1]), "component_path"),
        (("component:src/web/features/x/Y.test.tsx", SCREEN[1]), "component_path"),
        ((SCREEN[0], "test:src/web/features/x/Y.tsx"), "test_path"),
        (SCREEN + ("color:red",), "bad_ref"),
    ],
)
def test_each_ui_base_failure_has_a_code(refs, code):
    assert code in codes(verify_ui_base(refs))


def test_a_screen_needs_routes_to_read():
    assert "no_routes" in codes(verify_ui_base(SCREEN, authorization=None))


def web_tree(tmp_path, *, component=True, reads="tracks/", test_mentions="TrackPanel"):
    folder = tmp_path / "src/web/features/tracks"
    folder.mkdir(parents=True)
    if component:
        (folder / "TrackPanel.tsx").write_text(f'const url = base + "{reads}";\n')
    (folder / "TrackPanel.test.tsx").write_text(f"import {{ {test_mentions} }} from './x';\n")
    return tmp_path


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, []),
        ({"component": False}, ["component_missing"]),
        ({"reads": "elsewhere/"}, ["screen_reads_nothing"]),
        ({"test_mentions": "SomethingElse"}, ["test_unrelated"]),
    ],
)
def test_the_ui_ci_check_finds_a_missing_screen_one_that_reads_nothing_and_an_unrelated_test(
    isolated, tmp_path, options, expected
):
    web_tree(tmp_path, **options)
    claims = {
        "authorization": ft.provided(
            "route:track-list", "scope:event", "readers:members", "writers:admin,organizer",
            "narrow:track-list:POST=admin,organizer", "test:tests/x.py::test_y",
        ),
        "ui_base": ft.provided(*SCREEN),
    }  # fmt: skip
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "events.Track", claims))
    found = [p for p in ft.check_static(tmp_path) if p["property"] == "ui_base"]
    assert codes(found) == expected


# --- advanced UI (T02) ----------------------------------------------------------------------------

USES = (
    "uses:EntityGrid@src/web/features/event-builder/RegistrationPanel.tsx",
    "uses:NotesDialog@src/web/features/event-builder/RegistrationPanel.tsx",
)


def verify_advanced(refs):
    feature = ft.Feature("s", "S", "events.EventApplication", {"ui_advanced": ft.provided(*refs)})
    return ft.VERIFIERS["ui_advanced"](feature, feature.claims["ui_advanced"], ft.System())


def test_a_real_advanced_ui_claim_names_the_shared_component_and_the_screen_that_uses_it():
    assert verify_advanced(USES) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["form"]["facts"]["ui_advanced"]["uses"] == [
        "VersionCompare in FormBuilder.tsx",
        "PreviewBar in FormPreviewAs.tsx",
    ]
    assert row["track"]["facts"]["ui_advanced"]["advanced"] == "none beyond the base screen"
    assert row["announcement"]["claims"]["ui_advanced"]["state"] == "planned"


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (("no_advanced@short",), "no_reason"),
        (
            USES + ("no_advanced@a long enough reason why nothing sits beyond the base screen",),
            "both",
        ),
        ((), "no_uses"),
        (("uses:Wizard@src/web/features/a/B.tsx",), "component_unknown"),
        (("uses:EntityGrid@src/web/lib/x.ts",), "screen_path"),
        (("uses:EntityGrid@src/web/features/a/B.test.tsx",), "screen_path"),
        (USES + (USES[0],), "use_twice"),
        (USES + ("color:red",), "bad_ref"),
    ],
)
def test_each_advanced_ui_failure_has_a_code(refs, code):
    assert code in codes(verify_advanced(refs))


def advanced_tree(tmp_path, *, imports=True, reads=True, shared=True):
    (tmp_path / "src/web/components").mkdir(parents=True)
    (tmp_path / "src/web/features/regs").mkdir(parents=True)
    if shared:
        (tmp_path / "src/web/components/EntityGrid.tsx").write_text(
            "export const EntityGrid = 1;\n"
        )
    line = 'import { EntityGrid } from "../../components/EntityGrid";\n' if imports else ""
    body = 'const url = "applications/";\n' if reads else "const url = 1;\n"
    (tmp_path / "src/web/features/regs/Panel.tsx").write_text(line + body)


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, []),
        ({"imports": False}, ["not_imported"]),
        ({"reads": False}, ["screen_reads_nothing"]),
        ({"shared": False}, ["component_missing"]),
    ],
)
def test_the_advanced_ui_ci_check_finds_an_unimported_component_and_a_screen_that_reads_nothing(
    isolated, tmp_path, options, expected
):
    advanced_tree(tmp_path, **options)
    claims = {
        "authorization": ft.provided(
            "route:event-application-list", "scope:event", "readers:admin,organizer",
            "writers:admin,organizer", "test:tests/x.py::test_y",
        ),
        "ui_advanced": ft.provided("uses:EntityGrid@src/web/features/regs/Panel.tsx"),
    }  # fmt: skip
    ft.FEATURES.clear()
    ft.register_feature(ft.Feature("x", "X", "events.EventApplication", claims))
    found = [p for p in ft.check_static(tmp_path) if p["property"] == "ui_advanced"]
    assert codes(found) == expected
