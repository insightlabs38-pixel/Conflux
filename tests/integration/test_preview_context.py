"""PD-F002-B03-T01: previewing as a role, as of a time or at a kept version (one primitive)."""

import json
import random
import re
from datetime import UTC, datetime

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import preview_context as pc
from core import version_diff as vd
from django.test import Client
from events.models import Event
from forms.models import FormDefinition, FormVersion
from forms.services import create_form, publish_form, save_draft
from forms.validation import field_in_scope
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ALL = ["participant", "judge", "organizer"]
T1 = datetime(2027, 3, 1, 9, 0, tzinfo=UTC)
T2 = datetime(2027, 3, 8, 9, 0, tzinfo=UTC)


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def field(field_id, *, visible_to=None, **extra):
    return {
        "id": field_id, "label": field_id.title(), "visible_to": visible_to or ALL,
        **({"type": "text"} | extra),
    }  # fmt: skip


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    foreign = Workspace.objects.create(name="F", slug="f")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("admin", Role.ADMIN), ("par", Role.PARTICIPANT),
                       ("judge", Role.JUDGE)):  # fmt: skip
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["stranger"] = User.objects.create_user(username="stranger", password="unused")
    Membership.objects.create(user=people["stranger"], workspace=foreign, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    base = f"/api/v1/workspaces/{workspace.public_id}"
    return {
        "workspace": workspace, "event": event, "people": people,
        "url": lambda surface="form": f"{base}/preview-as/{surface}/",
    }  # fmt: skip


@pytest.fixture
def form(world):
    """Version 1 (March 1) with two fields, version 2 (March 8) adding a judge-only field, and a
    draft that adds an organizer-only one."""
    definition = create_form(world["event"], "Application")
    save_draft(definition, {"fields": [field("pitch"), field("repo", visible_to=["participant"])]})
    first = publish_form(definition)
    kind = field("kind", visible_to=[*ALL, "public"], type="select", options=["a", "b"])
    track = field(
        "track", visible_to=["public", "organizer"], visible_if={"field": "kind", "equals": "a"}
    )
    save_draft(
        definition,
        {
            "fields": [
                field("pitch"),
                kind,
                field("repo", visible_to=["participant"]),
                field("score_note", visible_to=["judge", "organizer"]),
                track,
            ]
        },
    )
    second = publish_form(definition)
    FormVersion.objects.filter(pk=first.pk).update(published_at=T1)
    FormVersion.objects.filter(pk=second.pk).update(published_at=T2)
    save_draft(definition, {"fields": [field("pitch"), field("secret", visible_to=["organizer"])]})
    return {"definition": definition, "first": first, "second": second}


def ask(world, form, who="org", surface="form", **body):
    body.setdefault("ref", {"event": str(world["event"].public_id),
                            "form": str(form["definition"].public_id)})  # fmt: skip
    return client_for(world["people"][who]).post(
        world["url"](surface), data=json.dumps(body), content_type="application/json"
    )


def ids(response):
    return [f["id"] for f in response.json()["data"]["fields"]]


# --- the primitive, with an independent surface -------------------------------------------------


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr(pc, "SURFACES", dict(pc.SURFACES))
    monkeypatch.setattr(vd, "SOURCES", dict(vd.SOURCES))


def a_surface(isolated, *, input_schema=None, roles=("viewer", "editor"), live=None, kept=None):
    """A surface for something that is not a form: three kept values and its own source."""
    kept = kept or [("a", T1, "one"), ("b", T2, "two")]
    infos = [
        vd.VersionInfo(i, f"Version {i}", at.isoformat().replace("+00:00", "Z"))
        for i, at, _ in kept
    ]
    values = {i: v for i, _, v in kept}

    def versions(user, workspace, ref):
        return None if ref.get("hidden") else infos

    def snapshot(user, workspace, ref, version_id):
        return (version_id in values, values.get(version_id))

    vd.register_source(vd.VersionSource("note", "Notes", ("note",), versions, snapshot))

    def resolve(user, workspace, ref, resolved, values_in):
        return {"text": resolved.value, "as": resolved.role, "input": values_in}

    surface = pc.Surface("note", "A note", ("note",), resolve, roles=roles, version_source="note",
                         input_schema=input_schema, live=live)  # fmt: skip
    pc.register_surface(surface)
    return surface


def run(raw=None, ref=None, input_raw=None):
    return pc.preview("note", None, None, ref or {"note": "n"}, raw, input_raw)


def test_a_surface_that_is_not_a_form_previews_through_the_same_primitive(isolated):
    a_surface(isolated)
    live = run()
    assert live.data == {"text": "two", "as": None, "input": {}}
    assert live.as_dict()["resolved"]["live"] is True
    assert live.as_dict()["summary"] == "Previewing Version b (live). Nothing is saved or sent."
    as_editor = run({"role": "editor", "version": "a"})
    assert as_editor.data["text"] == "one" and as_editor.data["as"] == "editor"
    assert (
        as_editor.as_dict()["summary"]
        == "Previewing as editor, Version a. Nothing is saved or sent."
    )
    assert [v["id"] for v in live.as_dict()["versions"]] == ["a", "b"]
    assert live.as_dict()["roles"] == ["viewer", "editor"]


def test_as_of_picks_the_latest_version_kept_at_or_before_that_time(isolated):
    a_surface(isolated)
    assert run({"at": "2027-03-04T00:00:00Z"}).data["text"] == "one"
    assert run({"at": "2027-03-08T09:00:00Z"}).data["text"] == "two"  # at the instant, inclusive
    assert run({"at": "2027-03-08T08:59:59Z"}).data["text"] == "one"
    assert run({"at": "2099-01-01T00:00:00Z"}).data["text"] == "two"
    offset = run({"at": "2027-03-08T10:00:00+01:00"})  # 09:00 UTC
    assert (
        offset.data["text"] == "two"
        and offset.as_dict()["resolved"]["at"] == "2027-03-08T09:00:00Z"
    )
    assert "as of 2027-03-08 09:00 UTC" in offset.as_dict()["summary"]
    assert (
        run({"at": "2027-03-04T00:00:00Z"}).as_dict()
        == run({"at": "2027-03-04T00:00:00Z"}).as_dict()
    )


def test_each_bad_context_part_is_named(isolated):
    a_surface(isolated)

    def problems(raw):
        with pytest.raises(pc.PreviewError) as caught:
            run(raw)
        return caught.value.problems

    assert list(problems({"role": "ghost"})) == ["context.role"]
    assert "viewer, editor" in problems({"role": "ghost"})["context.role"][0]
    assert list(problems({"at": "tomorrow"})) == ["context.at"]
    assert list(problems({"at": "2027-03-04T00:00:00"})) == ["context.at"]  # no offset
    assert list(problems({"at": "1999-12-31T23:59:59Z"})) == ["context.at"]
    assert list(problems({"at": 5})) == ["context.at"]
    assert (
        "first version was kept 2027-03-01T09:00:00Z"
        in problems({"at": "2027-01-01T00:00:00Z"})["context.at"][0]
    )
    assert problems({"version": "zzz"}) == {"context.version": ["No such version."]}
    assert problems({"version": "a", "at": "2027-03-04T00:00:00Z"}) == {
        "context.version": ["Choose a version or a time, not both."]
    }
    assert list(problems({"colour": "blue"})) == ["context.colour"]
    assert list(problems("nope")) == ["context"]
    assert set(problems({"role": "ghost", "at": "x", "colour": 1})) == {
        "context.role", "context.at", "context.colour",
    }  # fmt: skip


def test_an_unversioned_or_roleless_surface_refuses_what_it_cannot_do(isolated):
    pc.register_surface(pc.Surface("plain", "Plain", (), lambda *a: {"ok": True}))
    cases = (
        ({"role": "x"}, "context.role"),
        ({"at": "2027-03-04T00:00:00Z"}, "context.at"),
        ({"version": "v"}, "context.version"),
    )
    for raw, key in cases:
        with pytest.raises(pc.PreviewError) as caught:
            pc.preview("plain", None, None, {}, raw)
        assert list(caught.value.problems) == [key]
    assert pc.preview("plain", None, None, {}).data == {"ok": True}
    assert (
        pc.preview("plain", None, None, {})
        .as_dict()["summary"]
        .startswith("Previewing the live view")
    )


def test_the_live_default_is_the_surfaces_own_rule_and_an_unpublished_draft_says_so(isolated):
    surface = a_surface(isolated, live=lambda listed: listed[0])
    assert run().data["text"] == "one"
    assert surface.live is not None
    pc.SURFACES["note"] = pc.Surface("note", "A note", ("note",), surface.resolve,
                                     roles=surface.roles, version_source="note")  # fmt: skip
    vd.SOURCES["note"] = vd.VersionSource(
        "note",
        "Notes",
        ("note",),
        lambda u, w, r: [vd.VersionInfo("draft", "Current draft", current=True)],
        lambda u, w, r, v: (True, "wip"),
    )
    draft = run()
    assert draft.data["text"] == "wip" and [n["code"] for n in draft.notices] == ["unpublished"]


def test_a_surface_input_is_validated_by_the_schema_subset_and_normalised(isolated):
    limit = {"type": "integer", "minimum": 1, "maximum": 5, "default": 3}
    schema = {
        "type": "object",
        "properties": {"limit": limit, "note": {"type": "string", "maxLength": 5}},
        "additionalProperties": False,
    }
    a_surface(isolated, input_schema=schema)
    assert run().data["input"] == {"limit": 3}
    assert run(input_raw={"limit": 2, "note": "hi"}).data["input"] == {"limit": 2, "note": "hi"}
    with pytest.raises(pc.PreviewError) as caught:
        run(input_raw={"limit": 9, "note": "toolong", "extra": 1})
    assert set(caught.value.problems) == {"input", "input.limit", "input.note"}
    with pytest.raises(pc.PreviewError) as caught:
        run(input_raw={"note": "x" * 30_000})
    assert set(caught.value.problems) == {"input"}


def test_a_surface_without_an_input_schema_takes_none(isolated):
    a_surface(isolated)
    with pytest.raises(pc.PreviewError) as caught:
        run(input_raw={"anything": 1})
    assert caught.value.problems == {"input": ["This preview takes no input."]}


def test_what_the_source_hides_or_the_surface_declines_is_not_visible(isolated):
    a_surface(isolated)
    with pytest.raises(pc.NotVisible):
        run(ref={"note": "n", "hidden": "1"})
    with pytest.raises(pc.NotVisible):
        pc.preview("missing", None, None, {})
    pc.register_surface(pc.Surface("declines", "No", (), lambda *a: None))
    with pytest.raises(pc.NotVisible):
        pc.preview("declines", None, None, {})


def test_registration_is_strict(isolated):
    surface = a_surface(isolated)
    pc.register_surface(surface)  # the same object again is harmless
    with pytest.raises(ValueError):
        pc.register_surface(pc.Surface("note", "Other", (), surface.resolve))
    with pytest.raises(ValueError):
        pc.register_surface(pc.Surface("lost", "Lost", (), surface.resolve, version_source="nope"))


# --- the form surface through the endpoint ------------------------------------------------------


def test_each_role_sees_what_the_form_shows_that_role(world, form):
    expected = {
        "participant": ["pitch", "kind", "repo", "track"],
        "judge": ["pitch", "kind", "score_note", "track"],
        "public": ["kind", "track"],
        "organizer": ["pitch", "kind", "score_note", "track"],
    }
    for role, want in expected.items():
        response = ask(
            world, form, context={"role": role, "version": str(form["second"].public_id)}
        )
        assert response.status_code == 200, response.content
        assert ids(response) == want, role
        data = response.json()["data"]
        assert data["total"] == 5 and data["hidden"] == 5 - len(want)
    track = next(f for f in response.json()["data"]["fields"] if f["id"] == "track")
    assert track["visible_if"] == {"field": "kind", "equals": "a"}  # kept with its condition


def test_without_a_role_the_organizer_sees_the_whole_form(world, form):
    response = ask(world, form, context={"version": "draft"})
    assert ids(response) == ["pitch", "secret"] and response.json()["data"]["hidden"] == 0
    assert response.json()["resolved"]["version"]["current"] is True


def test_the_live_view_is_what_participants_get_and_names_its_version(world, form):
    body = ask(world, form).json()
    assert body["resolved"]["live"] is True
    assert body["resolved"]["version"]["label"] == "Version 2"
    assert [f["id"] for f in body["data"]["fields"]] == [
        "pitch",
        "kind",
        "repo",
        "score_note",
        "track",
    ]
    assert body["summary"] == "Previewing Version 2 (live). Nothing is saved or sent."
    assert [v["label"] for v in body["versions"]] == ["Version 1", "Version 2", "Current draft"]
    assert body["roles"] == ["participant", "judge", "organizer", "public"]


def test_as_of_a_time_shows_the_version_in_force_then(world, form):
    early = ask(world, form, context={"role": "judge", "at": "2027-03-03T00:00:00Z"}).json()
    assert early["resolved"]["version"]["label"] == "Version 1"
    assert [f["id"] for f in early["data"]["fields"]] == ["pitch"]  # no judge-only field yet
    assert "judge, Version 1, as of 2027-03-03 00:00 UTC" in early["summary"]
    late = ask(world, form, context={"role": "judge", "at": "2027-03-09T00:00:00Z"}).json()
    assert [f["id"] for f in late["data"]["fields"]] == ["pitch", "kind", "score_note", "track"]
    before = ask(world, form, context={"at": "2027-02-01T00:00:00Z"})
    assert before.status_code == 400
    assert "first version was kept 2027-03-01T09:00:00Z" in before.json()["context.at"][0]


def test_a_pinned_version_does_not_move_when_the_form_is_published_again(world, form):
    version = str(form["first"].public_id)
    before = ask(world, form, context={"version": version, "role": "participant"}).json()
    save_draft(form["definition"], {"fields": [field("only_now")]})
    publish_form(form["definition"])
    after = ask(world, form, context={"version": version, "role": "participant"}).json()
    for part in ("data", "resolved", "summary"):
        assert before[part] == after[part]
    assert len(after["versions"]) == len(before["versions"]) + 1  # the list moves, the pin does not
    assert ask(world, form).json()["resolved"]["version"]["label"] == "Version 3"


def test_a_role_never_sees_more_than_the_organizer_and_follows_the_forms_own_rule(world, form):
    rng = random.Random(7)
    organizer_ids = lambda response: set(ids(response))  # noqa: E731
    for round_ in range(40):
        fields = [
            field(
                f"f{i}",
                visible_to=rng.sample(
                    ["participant", "judge", "organizer", "public"], rng.randint(1, 3)
                ),
            )
            for i in range(rng.randint(1, 8))
        ]
        save_draft(form["definition"], {"fields": fields})
        everything = ask(world, form, context={"version": "draft"})
        for role in ("participant", "judge", "public", "organizer"):
            response = ask(world, form, context={"version": "draft", "role": role})
            assert organizer_ids(response) <= organizer_ids(everything)
            assert ids(response) == [f["id"] for f in fields if field_in_scope(f, role)], round_


def test_only_organizers_and_admins_preview_and_everything_else_is_404_or_403(world, form):
    for who in ("org", "admin"):
        assert ask(world, form, who).status_code == 200
    for who in ("par", "judge", "stranger"):
        assert ask(world, form, who).status_code == 403, who
    assert Client().post(
        world["url"](), data="{}", content_type="application/json"
    ).status_code in (401, 403)
    assert ask(world, form, surface="nope").status_code == 404
    other = Event.objects.create(
        workspace=Workspace.objects.create(name="X", slug="x"), name="O", slug="o"
    )
    foreign = {"event": str(other.public_id), "form": str(form["definition"].public_id)}
    assert ask(world, form, ref=foreign).status_code == 404
    unknown = {
        "event": str(world["event"].public_id),
        "form": "00000000-0000-4000-8000-000000000000",
    }
    assert ask(world, form, ref=unknown).status_code == 404


def test_bad_requests_name_the_part_to_fix(world, form):
    assert ask(world, form, ref={}).json() == {
        "ref.event": ["This value is required."], "ref.form": ["This value is required."],
    }  # fmt: skip
    assert ask(world, form, ref="x").status_code == 400
    assert list(ask(world, form, context={"role": "king"}).json()) == ["context.role"]
    assert list(ask(world, form, context={"version": "nope"}).json()) == ["context.version"]
    assert ask(world, form, input={"a": 1}).json() == {"input": ["This preview takes no input."]}
    org = client_for(world["people"]["org"])
    assert org.get(world["url"]()).status_code == 405
    for method in ("put", "patch", "delete"):
        assert getattr(org, method)(world["url"]()).status_code == 405


def test_a_preview_writes_nothing_acts_as_nobody_else_and_is_never_cached(world, form):
    before = (
        AuditEvent.objects.count(),
        FormDefinition.objects.count(),
        FormVersion.objects.count(),
    )
    draft = form["definition"].draft_schema
    org = client_for(world["people"]["org"])
    response = org.post(
        world["url"](),
        data=json.dumps(
            {
                "ref": {
                    "event": str(world["event"].public_id),
                    "form": str(form["definition"].public_id),
                },
                "context": {"role": "participant"},
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert "Set-Cookie" not in response and not response.cookies
    form["definition"].refresh_from_db()
    assert form["definition"].draft_schema == draft
    assert (
        AuditEvent.objects.count(),
        FormDefinition.objects.count(),
        FormVersion.objects.count(),
    ) == before
    # The caller stayed themselves: a role they do not hold gives no extra reach elsewhere.
    assert org.get(f"/api/v1/workspaces/{world['workspace'].public_id}/events/").status_code == 200
    par = client_for(world["people"]["par"])
    assert par.post(world["url"](), data="{}", content_type="application/json").status_code == 403


def test_no_domain_code_reads_a_preview_context():
    """A context lives in this endpoint's body: only core and the registered surface touch it."""
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[2] / "src" / "api"
    users = sorted(
        str(p.relative_to(src))
        for p in src.rglob("*.py")
        if "preview_context" in p.read_text() and "migrations" not in p.parts
        and not p.name.startswith("test_")
    )  # fmt: skip
    assert users == [
        "core/manifest_core.py", "core/preview_context.py", "core/preview_context_views.py",
        "core/urls.py", "forms/preview.py",
    ]  # fmt: skip
    for p in src.rglob("*.py"):
        if "migrations" in p.parts or p.name.startswith("test_"):
            continue
        text = p.read_text()
        for needle in (r"\bas_role\b", "X-Preview", "preview_as_user", r"session\[.preview"):
            assert not re.search(needle, text), (p, needle)


def test_the_inventory_lists_the_surface_and_the_forms_manifest_claims_it(world):
    from core import manifest

    snapshot = manifest.snapshot()
    kinds = {
        c["kind"]: {e["id"]: e["manifest"] for e in c["entries"]} for c in snapshot["capabilities"]
    }
    assert kinds["preview_surface"] == {"form": "forms"} and snapshot["ok"] is True
