"""PD-F002-B02-T05: comparing versions through one primitive, two sources and the config history."""

import json
import pathlib
import random

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import version_diff as vd
from django.test import Client
from evaluations.models import EvaluationPlan, RubricVersion
from evaluations.rubric import clean_criteria
from events.models import Event
from forms.services import create_form, publish_form, save_draft
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/fixtures/diff_cases.json").read_text())["cases"]
RUN = {"json": vd.diff_json, "text": vd.diff_text, "value": vd.diff_value}


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_the_shared_fixtures_hold(case):
    """The same file is drawn by vitest (components/DiffView.test.tsx) from the server diffs."""
    assert RUN[case["kind"]](case["before"], case["after"]) == case["diff"]


# --- properties of the pure functions ---------------------------------------------------------


def apply_changes(before, changes):
    """A small, independent applier of json diffs (lists without identity): proves the paths."""
    import copy

    value = copy.deepcopy(before)

    def parts(path):
        return [p.replace("~1", "/").replace("~0", "~") for p in path.split("/")[1:]]

    def walk(root, keys):
        node = root
        for key in keys:
            node = node[int(key)] if isinstance(node, list) else node[key]
        return node

    for change in sorted(changes, key=lambda c: (c["op"] == "removed", c["path"]), reverse=False):
        keys = parts(change["path"])
        if not keys:
            return change["after"]
        parent, last = walk(value, keys[:-1]), keys[-1]
        if isinstance(parent, list):
            last = int(last)
        if change["op"] == "removed":
            continue
        if isinstance(parent, list) and change["op"] == "added":
            parent.insert(last, change["after"]) if last <= len(parent) else parent.append(
                change["after"]
            )
        else:
            parent[last] = change["after"]
    for change in sorted(
        (c for c in changes if c["op"] == "removed"), key=lambda c: c["path"], reverse=True
    ):
        keys = parts(change["path"])
        parent, last = walk(value, keys[:-1]), keys[-1]
        if isinstance(parent, list):
            del parent[int(last)]
        else:
            del parent[last]
    return value


def random_json(rng, depth=0):
    kinds = ["int", "str", "bool", "null"] + (["dict", "list"] if depth < 3 else [])
    kind = rng.choice(kinds)
    if kind == "int":
        return rng.randint(0, 5)
    if kind == "str":
        return rng.choice(["a", "b", "c d"])
    if kind == "bool":
        return rng.random() < 0.5
    if kind == "null":
        return None
    if kind == "list":
        return [random_json(rng, depth + 1) for _ in range(rng.randint(0, 4))]
    return {rng.choice("abcde"): random_json(rng, depth + 1) for _ in range(rng.randint(0, 4))}


def test_a_diff_of_equal_values_is_empty_and_applying_a_diff_rebuilds_the_after_value():
    rng = random.Random(3)
    for _ in range(300):
        before, after = random_json(rng), random_json(rng)
        diff = vd.diff_json(before, after)
        assert diff == vd.diff_json(before, after)  # deterministic
        assert vd.diff_json(before, before)["changes"] == []
        assert not diff["truncated"]
        assert apply_changes(before, diff["changes"]) == after, (before, after, diff)


def test_changes_are_in_a_stable_order_whatever_the_key_order():
    one = vd.diff_json({"b": 1, "a": 1}, {"a": 2, "b": 2})
    two = vd.diff_json({"a": 1, "b": 1}, {"b": 2, "a": 2})
    assert one == two and [c["path"] for c in one["changes"]] == ["/a", "/b"]


def test_the_number_of_changes_is_capped_but_still_counted():
    diff = vd.diff_json({}, {f"k{i}": i for i in range(vd.MAX_CHANGES + 100)})
    assert len(diff["changes"]) == vd.MAX_CHANGES and diff["total"] == vd.MAX_CHANGES + 100
    assert diff["truncated"] is True


def test_large_values_are_clipped_and_flagged():
    diff = vd.diff_json({"v": "a" * 5000}, {"v": "b" * 5000})
    change = diff["changes"][0]
    assert change["clipped"] is True and len(change["before"]) == vd.MAX_VALUE_CHARS
    added = vd.diff_json({}, {"v": {"rows": list(range(2000))}})["changes"][0]
    assert added["clipped"] is True and added["after"].endswith("…")


def test_very_deep_values_are_compared_as_one_value_not_recursed_into():
    def nest(leaf, depth=60):
        value = leaf
        for _ in range(depth):
            value = {"n": value}
        return value

    diff = vd.diff_json(nest(1), nest(2))
    assert diff["total"] == 1 and diff["changes"][0]["op"] == "changed"
    assert diff["changes"][0]["path"].count("/") == vd.MAX_DEPTH


def test_keyed_lists_survive_hundreds_of_items_quickly():
    before = [{"id": f"f{i}", "label": f"F{i}"} for i in range(500)]
    after = [before[-1], *before[:-1]]
    diff = vd.diff_json({"fields": before}, {"fields": after})
    assert [c["op"] for c in diff["changes"]] == ["moved"]


def test_text_beyond_the_limits_is_refused_with_a_code():
    with pytest.raises(vd.DiffError) as caught:
        vd.diff_text("x\n" * (vd.MAX_LINES + 1), "")
    assert caught.value.code == "too_large"
    with pytest.raises(vd.DiffError):
        vd.diff_text("", "y" * (vd.MAX_TEXT_CHARS + 1))
    # A value too large to line-diff falls back to one clipped change, never an error.
    big = "line\n" * 6000
    assert vd.diff_value(big, big + "more")["kind"] == "json"


def test_long_lines_and_huge_hunks_are_bounded():
    diff = vd.diff_text("a" * 2000, "b" * 2000)
    assert all(len(line["text"]) <= vd.MAX_LINE_CHARS for h in diff["hunks"] for line in h["lines"])
    many = vd.diff_text(
        "\n".join(f"a{i}" for i in range(4000)), "\n".join(f"b{i}" for i in range(4000))
    )
    assert many["truncated"] is True
    assert sum(len(h["lines"]) for h in many["hunks"]) <= vd.MAX_HUNK_LINES
    assert many["added"] == 4000 and many["removed"] == 4000


def test_diffing_never_mutates_or_raises_on_hostile_json():
    rng = random.Random(5)
    for _ in range(200):
        before, after = random_json(rng), random_json(rng)
        import copy

        snapshot = copy.deepcopy((before, after))
        vd.diff_value(before, after)
        assert (before, after) == snapshot


# --- sources and endpoints --------------------------------------------------------------------


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world(db):
    workspace = Workspace.objects.create(name="W", slug="w")
    foreign = Workspace.objects.create(name="F", slug="f")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("par", Role.PARTICIPANT), ("judge", Role.JUDGE)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["stranger"] = User.objects.create_user(username="stranger", password="unused")
    Membership.objects.create(user=people["stranger"], workspace=foreign, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    return {"workspace": workspace, "event": event, "people": people}


def get(world, who, source, suffix="", **query):
    from urllib.parse import urlencode

    url = f"/api/v1/workspaces/{world['workspace'].public_id}/versions/{source}/{suffix}"
    return client_for(world["people"][who]).get(url + "?" + urlencode(query))


FIELD_A = {"id": "pitch", "type": "text", "label": "Pitch"}
FIELD_B = {"id": "url", "type": "url", "label": "URL"}


@pytest.fixture
def form(world):
    form = create_form(world["event"], "Application")
    save_draft(form, {"fields": [FIELD_A]})
    first = publish_form(form)
    save_draft(form, {"fields": [{**FIELD_A, "label": "Your pitch"}, FIELD_B]})
    second = publish_form(form)
    save_draft(form, {"fields": [FIELD_B, {**FIELD_A, "label": "Your pitch"}]})
    return {"form": form, "v1": first, "v2": second}


def form_query(world, form):
    return {"event": world["event"].public_id, "form": form["form"].public_id}


def test_a_form_lists_its_published_versions_then_the_live_draft(world, form):
    body = get(world, "org", "form", **form_query(world, form)).json()
    assert body["source"] == "form" and body["label"] == "Form versions"
    assert [(v["label"], v["current"]) for v in body["versions"]] == [
        ("Version 1", False), ("Version 2", False), ("Current draft", True),
    ]  # fmt: skip
    assert body["versions"][0]["id"] == str(form["v1"].public_id)
    assert body["versions"][2]["id"] == "draft"


def test_two_form_versions_are_compared_by_field_identity(world, form):
    query = form_query(world, form)
    response = get(
        world,
        "org",
        "form",
        "diff/",
        **query,
        **{"older": form["v1"].public_id, "newer": form["v2"].public_id},
    )
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    body = response.json()
    assert body["older"]["label"] == "Version 1" and body["newer"]["label"] == "Version 2"
    assert [(c["path"], c["op"]) for c in body["diff"]["changes"]] == [
        ("/fields/0/label", "changed"), ("/fields/1", "added"),
    ]  # fmt: skip
    draft = get(
        world, "org", "form", "diff/", **query, **{"older": form["v2"].public_id, "newer": "draft"}
    )
    assert [(c["path"], c["op"]) for c in draft.json()["diff"]["changes"]] == [
        ("/fields/0", "moved")
    ]
    assert draft.json()["newer"]["current"] is True


def test_a_comparison_reads_only_and_audits_nothing(world, form):
    audits = AuditEvent.objects.count()
    versions = form["form"].versions.count()
    query = form_query(world, form)
    get(world, "org", "form", "diff/", **query, **{"older": "draft", "newer": "draft"})
    assert AuditEvent.objects.count() == audits and form["form"].versions.count() == versions
    same = get(
        world, "org", "form", "diff/", **query, **{"older": "draft", "newer": "draft"}
    ).json()
    assert same["diff"]["changes"] == [] and same["diff"]["total"] == 0


def test_only_organizers_of_the_workspace_may_compare_and_others_learn_nothing(world, form):
    query = form_query(world, form)
    ids = {"older": form["v1"].public_id, "newer": "draft"}
    for who in ("par", "judge"):
        assert get(world, who, "form", **query).status_code == 404
        assert get(world, who, "form", "diff/", **query, **ids).status_code == 404
    assert get(world, "stranger", "form", **query).status_code == 403
    assert Client().get(
        f"/api/v1/workspaces/{world['workspace'].public_id}/versions/form/"
    ).status_code in (401, 403)


def test_bad_requests_name_the_parameter_or_are_simply_not_found(world, form):
    query = form_query(world, form)
    assert get(world, "org", "form").status_code == 400
    assert set(get(world, "org", "form", event=query["event"]).json()) == {"form"}
    assert set(get(world, "org", "form", "diff/", **query).json()) == {"older", "newer"}
    assert (
        get(
            world, "org", "form", "diff/", **query, **{"older": "nope", "newer": "draft"}
        ).status_code
        == 404
    )
    assert (
        get(world, "org", "form", "diff/", **query, **{"older": "draft", "newer": "99"}).status_code
        == 404
    )
    assert get(world, "org", "wiki", **query).status_code == 404
    other = Event.objects.create(workspace=world["workspace"], name="E2", slug="e2")
    wrong = get(world, "org", "form", event=other.public_id, form=form["form"].public_id)
    assert wrong.status_code == 404
    junk = get(world, "org", "form", event="x", form="y")
    assert junk.status_code == 404


def test_rubric_versions_compare_by_criterion_id(world):
    stage = Stage.objects.create(event=world["event"], name="Finals")
    one = [{"id": "impact", "name": "Impact", "weight": 2, "min_score": 0, "max_score": 10}]
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging", draft_criteria=one)
    v1 = RubricVersion.objects.create(plan=plan, number=1, criteria=one)
    two = [
        {"id": "craft", "name": "Craft", "weight": 1, "min_score": 0, "max_score": 5},
        {**one[0], "weight": 3},
    ]
    # The API stores the cleaned form; so does a published version (`anchors` is filled in).
    EvaluationPlan.objects.filter(pk=plan.pk).update(draft_criteria=clean_criteria(two))
    query = {"event": world["event"].public_id, "plan": plan.public_id}
    listed = get(world, "org", "rubric", **query).json()["versions"]
    assert [v["label"] for v in listed] == ["Version 1", "Current draft"]
    body = get(
        world, "org", "rubric", "diff/", **query, **{"older": v1.public_id, "newer": "draft"}
    ).json()
    assert [(c["path"], c["op"]) for c in body["diff"]["changes"]] == [
        ("/criteria/0", "added"), ("/criteria/1/weight", "changed"),
    ]  # fmt: skip
    assert body["diff"]["changes"][1]["before"] == 2 and body["diff"]["changes"][1]["after"] == 3
    assert get(world, "judge", "rubric", **query).status_code == 404
    assert get(world, "stranger", "rubric", **query).status_code == 403


def test_a_feature_registers_its_own_source_with_no_private_coupling(world):
    """An independent consumer: a text resource with two versions."""
    texts = {"1": "intro\nbody\n", "2": "intro\nbody changed\nfooter\n"}

    def versions(user, workspace, ref):
        return (
            [vd.VersionInfo("1", "First"), vd.VersionInfo("2", "Second")]
            if ref["doc"] == "d"
            else None
        )

    def snapshot(user, workspace, ref, version_id):
        return (True, texts[version_id]) if version_id in texts else (False, None)

    source = vd.VersionSource("test_doc", "Doc", ("doc",), versions, snapshot, kind="text")
    vd.register_source(source)
    try:
        vd.register_source(source)
        with pytest.raises(ValueError):
            vd.register_source(vd.VersionSource("test_doc", "Other", ("doc",), versions, snapshot))
        body = get(
            world, "par", "test_doc", "diff/", doc="d", **{"older": "1", "newer": "2"}
        ).json()
        assert (
            body["diff"]["kind"] == "text"
            and body["diff"]["added"] == 2
            and body["diff"]["removed"] == 1
        )
        assert get(world, "par", "test_doc", doc="other").status_code == 404
    finally:
        vd.SOURCES.pop("test_doc", None)


# --- the configuration history: the flat before/after, now with a structured diff --------------


def test_a_configuration_change_carries_the_diff_of_every_changed_field(world):
    workspace, event, org = world["workspace"], world["event"], world["people"]["org"]
    client = client_for(org)
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    client.patch(
        base, {"name": "Hack 2.0", "timezone": "America/New_York"}, content_type="application/json"
    )
    entries = client.get(
        f"/api/v1/audit/{workspace.public_id}/events/{event.public_id}/config-history/"
    ).json()
    entry = entries[0]
    assert set(entry["diff"]) == set(entry["changes"])
    name = entry["diff"]["name"]
    assert name["kind"] == "json" and name["changes"] == [
        {"path": "", "op": "changed", "before": "E", "after": "Hack 2.0", "clipped": False}
    ]
    for field, change in entry["changes"].items():  # the flat form is unchanged and agrees
        only = entry["diff"][field]["changes"]
        assert only[0]["before"] == change["before"] and only[0]["after"] == change["after"]


def test_prose_in_a_configuration_change_is_a_line_diff(world):
    workspace, event, org = world["workspace"], world["event"], world["people"]["org"]
    client = client_for(org)
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    client.patch(base, {"description": "Line one\nLine two\n"}, content_type="application/json")
    client.patch(
        base, {"description": "Line one\nLine 2\nLine three\n"}, content_type="application/json"
    )
    entries = client.get(
        f"/api/v1/audit/{workspace.public_id}/events/{event.public_id}/config-history/"
    ).json()
    diff = entries[0]["diff"]["description"]
    assert diff["kind"] == "text" and (diff["added"], diff["removed"]) == (2, 1)
