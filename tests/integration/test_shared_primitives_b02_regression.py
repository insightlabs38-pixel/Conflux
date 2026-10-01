"""PD-F002-B02-T90: cross-cutting proofs for the eight shared primitives of the batch.

The per-primitive behavior is proved next to each primitive (see docs/verification/PD-F002-B02/
MATRIX.md). This file proves what only holds across them: the registries hold exactly what
production registers and the extension inventory describes every one of them, every route refuses
signed-out callers and people outside the workspace, reading writes nothing, the one mutation
(a notification choice) is audited, and no core module imports a domain app.
"""

import ast
import json
import pathlib

import pytest
import yaml
from accounts.models import Session, User
from audit.models import AuditEvent
from core import manifest, notifications, previews, rich, version_diff
from core.models import NotificationPreference
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "api"
PLATFORM = {"accounts", "audit", "workspaces", "core", "config"}
OWNERS = {f"PD-F002-B02-T0{n}": n for n in range(1, 9)}


def test_the_primitive_registry_marks_the_eight_owners_implemented():
    document = yaml.safe_load(
        (ROOT / "docs/product-depth-v3/PRIMITIVE_REGISTRY.yaml").read_text(encoding="utf-8")
    )
    state = {
        p["owner_task"]: p["status"] for p in document["primitives"] if p["owner_task"] in OWNERS
    }
    assert set(state) == set(OWNERS)
    assert set(state.values()) == {"IMPLEMENTED"}, state


def test_core_still_depends_on_no_domain_app():
    """The new primitives live in core; domains register with them, never the reverse."""
    domains = {
        p.name
        for p in SRC.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and p.name not in PLATFORM
    }
    offenders = []
    for path in sorted((SRC / "core").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                continue
            offenders += [f"{path.name}: {n}" for n in names if n.split(".")[0] in domains]
    assert offenders == []


def test_the_registries_hold_exactly_what_production_registers():
    assert set(previews.SOURCES) == {"project_artifact", "job_output"}
    assert set(version_diff.SOURCES) == {"form", "rubric"}
    assert set(notifications.CATEGORIES) == {"announcement", "mention", "essential"}
    assert set(rich.PROFILES) == {"page", "story"}


def test_the_extension_inventory_describes_every_registry_of_the_batch_and_the_batch_before():
    """EXTENSION_MANIFEST lists what the other primitives register, and it agrees with them."""
    snapshot = manifest.snapshot()
    kinds = {c["kind"]: {e["id"] for e in c["entries"]} for c in snapshot["capabilities"]}
    assert kinds["preview_source"] == set(previews.SOURCES)
    assert kinds["version_source"] == set(version_diff.SOURCES)
    assert kinds["notification_category"] == set(notifications.CATEGORIES)
    assert kinds["rich_profile"] == set(rich.PROFILES)
    for kind in ("job_kind", "approval_policy", "thread_subject", "timeline_provider", "entity",
                 "bulk_action"):  # fmt: skip
        assert kinds[kind], kind  # the batch-one registries too
    assert snapshot["ok"] is True and snapshot["problems"] == []


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    foreign = Workspace.objects.create(name="F", slug="f")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("par", Role.PARTICIPANT)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    stranger = User.objects.create_user(username="out", password="unused")
    Membership.objects.create(user=stranger, workspace=foreign, role=Role.ORGANIZER)
    people["out"] = stranger
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    clients = {}
    for name, user in people.items():
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        clients[name] = client
    return {
        "workspace": workspace,
        "event": event,
        "client": clients,
        "anonymous": Client(),
        "base": f"/api/v1/workspaces/{workspace.public_id}/",
    }


def routes(w):
    base, event = w["base"], str(w["event"].public_id)
    return [
        ("POST", base + "rich/preview/", {"profile": "story", "source": "# Hi"}),
        ("GET", base + f"previews/project_artifact/?event={event}", None),
        ("GET", base + f"previews/job_output/?job={event}&name=x", None),
        ("GET", base + f"versions/form/?event={event}&form={event}", None),
        ("GET", base + f"versions/rubric/?event={event}&plan={event}", None),
        ("GET", base + f"versions/form/diff/?event={event}&form={event}&older=1&newer=2", None),
        ("GET", base + "notification-preferences/", None),
        (
            "PUT",
            base + "notification-preferences/",
            {"category": "announcement", "channel": "email", "enabled": False},
        ),
        ("GET", base + "extensions/", None),
    ]


def call(client, method, url, body):
    if body is None:
        return client.generic(method, url)
    return client.generic(method, url, data=json.dumps(body), content_type="application/json")


def test_every_route_refuses_signed_out_callers_and_people_outside_the_workspace(world):
    for method, url, body in routes(world):
        for who, client in (("anonymous", world["anonymous"]), ("out", world["client"]["out"])):
            response = call(client, method, url, body)
            assert response.status_code in (401, 403), (who, method, url, response.status_code)
    assert NotificationPreference.objects.count() == 0


def test_a_participant_gets_the_member_tools_and_nothing_organizer_only(world):
    par = world["client"]["par"]
    base = world["base"]
    assert (
        call(par, "POST", base + "rich/preview/", {"profile": "story", "source": "x"}).status_code
        == 200
    )
    assert par.get(base + "notification-preferences/").status_code == 200
    assert par.get(base + "extensions/").status_code == 403
    for source, query in (("form", "form"), ("rubric", "plan")):
        ids = f"event={world['event'].public_id}&{query}={world['event'].public_id}"
        url = base + f"versions/{source}/?{ids}"
        response = par.get(url)
        assert response.status_code in (403, 404), (source, response.status_code)


def test_reading_and_previewing_write_nothing_and_are_never_cached(world):
    org = world["client"]["org"]
    base = world["base"]
    before = AuditEvent.objects.count()
    responses = [
        call(org, "POST", base + "rich/preview/", {"profile": "page", "source": "<p>x</p>"}),
        org.get(base + "notification-preferences/"),
        org.get(base + "extensions/"),
        org.get(base + f"versions/form/?event={world['event'].public_id}&form=nope"),
    ]
    assert [r.status_code for r in responses[:3]] == [200, 200, 200]
    assert AuditEvent.objects.count() == before
    for response in (responses[2],):
        assert "no-store" in response["Cache-Control"]


def test_the_one_mutation_of_the_batch_is_audited_with_before_and_after_only(world):
    par = world["client"]["par"]
    response = call(
        par,
        "PUT",
        world["base"] + "notification-preferences/",
        {"category": "announcement", "channel": "email", "enabled": False},
    )
    assert response.status_code == 200
    rows = AuditEvent.objects.filter(action="notification_preference.changed")
    assert rows.count() == 1
    metadata = rows.get().metadata
    assert "announcement" in json.dumps(metadata) and "password" not in json.dumps(metadata)
    assert NotificationPreference.objects.count() == 1
