"""PD-F002-B01-T90: cross-cutting proofs for the eight shared primitives of the batch.

The per-primitive behavior is proved next to each primitive (see docs/verification/PD-F002-B01/
MATRIX.md). This file proves what only holds across them: the dependency direction, that the
registries hold exactly what production registers, that every route refuses the people it should,
and that every mutation leaves an audit record.
"""

import ast
import json
import pathlib

import pytest
import yaml
from accounts.models import Session, User
from audit.models import AuditEvent
from communications import bulk
from core import approvals, entities, jobs, threads, timeline
from django.test import Client
from events.models import Event
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "api"
PLATFORM = {"accounts", "audit", "workspaces", "core", "config"}


def test_core_depends_on_no_domain_app():
    """Domains register with core; core never imports a domain app (ESC-20260930-004)."""
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
    assert set(bulk.ACTIONS) == {"assign", "advance", "extend", "move", "send"}
    assert set(jobs.KINDS) == {"archive_export"}
    assert set(approvals.POLICIES) == {"message_send"}
    assert set(threads.SUBJECTS) == {"application", "project"}
    assert set(timeline.PROVIDERS) == {
        "event", "gate", "publication", "agenda", "office_hours", "voting", "reminder",
    }  # fmt: skip
    assert {"applications", "projects"} <= set(entities.entities())
    assert len(timeline.RULES) == 1  # the generic rules are built in; one domain rule registered


def test_the_primitive_registry_marks_the_eight_owners_implemented():
    document = yaml.safe_load(
        (ROOT / "docs/product-depth-v3/PRIMITIVE_REGISTRY.yaml").read_text(encoding="utf-8")
    )
    owners = {f"PD-F002-B01-T0{n}" for n in range(1, 9)}
    state = {
        p["owner_task"]: p["status"] for p in document["primitives"] if p["owner_task"] in owners
    }
    assert set(state) == owners
    assert set(state.values()) == {"IMPLEMENTED"}, state


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    people = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("org2", Role.ORGANIZER),
        ("par", Role.PARTICIPANT),
    ):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["out"] = User.objects.create_user(username="out", password="unused")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    project = Project.objects.create(event=event, name="P", created_by=people["par"])
    clients = {}
    for name, user in people.items():
        c = Client()
        c.cookies["session"] = Session.issue(user).token
        clients[name] = c
    return {
        "workspace": workspace,
        "event": event,
        "project": project,
        "client": clients,
        "anonymous": Client(),
        "base": f"/api/v1/workspaces/{workspace.public_id}/",
        "ev": f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/",
    }


def routes(w):
    thread = w["ev"] + f"threads/project/{w['project'].public_id}/organizers/"
    return [
        ("GET", w["ev"] + "entities/", None),
        ("GET", w["ev"] + "entities/projects/", None),
        ("GET", w["ev"] + "views/", None),
        ("POST", w["ev"] + "views/", {"entity": "projects", "name": "v", "query": {}}),
        ("GET", w["base"] + "jobs/", None),
        ("POST", w["ev"] + "archive/export-jobs/", {"mode": "config"}),
        ("GET", w["ev"] + "approvals/", None),
        ("GET", w["ev"] + "approval-gates/", None),
        ("PUT", w["ev"] + "approval-gates/message_send/", {"enabled": True}),
        ("GET", w["ev"] + "timeline/", None),
        ("GET", thread, None),
        ("POST", thread, {"body": "x"}),
        ("GET", w["ev"] + "operations/bulk/receipts/", None),
        ("POST", w["ev"] + "operations/bulk/", {"operations": []}),
    ]


def call(client, method, url, body):
    if body is None:
        return client.generic(method, url)
    return client.generic(method, url, data=json.dumps(body), content_type="application/json")


def test_every_route_refuses_signed_out_callers_and_people_outside_the_workspace(world):
    table = routes(world)
    for method, url, body in table:
        for who in ("anonymous", "out"):
            response = call(
                world["anonymous"] if who == "anonymous" else world["client"]["out"],
                method,
                url,
                body,
            )
            assert response.status_code in (401, 403), (who, method, url, response.status_code)


def test_organizer_only_routes_refuse_a_participant_and_nothing_is_leaked(world):
    table = routes(world)
    refused = {
        "archive/export-jobs/", "approval-gates/", "timeline/", "operations/bulk/receipts/",
        "operations/bulk/",
    }  # fmt: skip
    for method, url, body in table:
        if any(url.endswith(path) or path in url for path in refused):
            response = call(world["client"]["par"], method, url, body)
            assert response.status_code == 403, (method, url, response.status_code)
    # A participant sees no approval requests and no organizer notes, and learns nothing about them.
    assert world["client"]["par"].get(world["ev"] + "approvals/").json() == []
    notes = world["ev"] + f"threads/project/{world['project'].public_id}/organizers/"
    assert world["client"]["par"].get(notes).status_code == 404
    assert world["client"]["par"].get(world["base"] + "jobs/").json() == []


def test_every_mutating_primitive_leaves_an_audit_record(world):
    org, org2 = world["client"]["org"], world["client"]["org2"]
    ev = world["ev"]

    org.post(
        ev + "views/",
        data=json.dumps({"entity": "projects", "name": "v", "query": {}}),
        content_type="application/json",
    )
    org.post(
        ev + "archive/export-jobs/",
        data=json.dumps({"mode": "config"}),
        content_type="application/json",
    )
    org.put(
        ev + "approval-gates/message_send/",
        data=json.dumps({"enabled": True}),
        content_type="application/json",
    )
    held = org.post(
        ev + "communications/messages/",
        data=json.dumps({"subject": "s", "body": "b", "audience_kind": "all_participants"}),
        content_type="application/json",
    )
    assert held.status_code == 409
    org2.post(
        ev + f"approvals/{held.json()['approval']['public_id']}/decision/",
        data=json.dumps({"decision": "approve"}),
        content_type="application/json",
    )
    org.post(
        ev + f"threads/project/{world['project'].public_id}/organizers/",
        data=json.dumps({"body": "note"}),
        content_type="application/json",
    )
    track = org.post(
        ev + "tracks/", data=json.dumps({"name": "T"}), content_type="application/json"
    ).json()
    move = {
        "operations": [
            {
                "action": "move",
                "projects": [str(world["project"].public_id)],
                "track": track["public_id"],
            }
        ]
    }
    plan = org.post(ev + "operations/bulk/", data=json.dumps(move), content_type="application/json")
    token = plan.json()["preview_token"]
    applied = org.post(
        ev + "operations/bulk/",
        data=json.dumps({**move, "preview_token": token}),
        content_type="application/json",
    )
    assert applied.status_code == 200
    actions = set(AuditEvent.objects.values_list("action", flat=True))
    assert {
        "saved_view.created",
        "job.requested",
        "approval.gate_changed",
        "approval.requested",
        "approval.approved",
        "thread.comment_posted",
        "operations.bulk_applied",
    } <= actions, sorted(actions)
    # Audit never carries comment text.
    assert "note" not in str(
        list(
            AuditEvent.objects.filter(action="thread.comment_posted").values_list(
                "metadata", flat=True
            )
        )
    )


def test_an_archived_event_refuses_what_the_primitives_would_change(world):
    ev = world["ev"]
    Event.objects.filter(pk=world["event"].pk).update(status="archived")
    org = world["client"]["org"]
    assert (
        org.put(
            ev + "approval-gates/message_send/",
            data=json.dumps({"enabled": True}),
            content_type="application/json",
        ).status_code
        == 400
    )
    assert (
        org.post(
            ev + f"threads/project/{world['project'].public_id}/organizers/",
            data=json.dumps({"body": "x"}),
            content_type="application/json",
        ).status_code
        == 400
    )
    assert (
        org.post(
            ev + "operations/bulk/",
            data=json.dumps({"operations": []}),
            content_type="application/json",
        ).status_code
        == 400
    )
    # Reading stays possible, and an archive can still be exported as a job.
    assert org.get(ev + "timeline/").status_code == 200
    assert org.get(ev + "entities/projects/").status_code == 200
    assert (
        org.post(
            ev + "archive/export-jobs/",
            data=json.dumps({"mode": "config"}),
            content_type="application/json",
        ).status_code
        == 202
    )
