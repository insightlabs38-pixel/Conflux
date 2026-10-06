"""PD-F003-B01-T03: the authorization claims of the completeness contract, held against real
requests. The permission matrix says who may reach each route; these tests send the requests."""

import json
import uuid

import pytest
from accounts.models import Session, User
from core import features as ft
from django.test import Client
from django.urls import reverse
from events.models import Event
from projects.models import Project, ProjectMembership
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

WRITES = ("POST", "PUT", "PATCH", "DELETE")


def client_for(user=None):
    client = Client()
    if user is not None:
        client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    people = {}
    for role in Role.values:
        user = User.objects.create_user(username=f"u-{role}", password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[role] = user
    stranger = User.objects.create_user(username="stranger", password="unused")
    return {"workspace": workspace, "event": event, "people": people, "stranger": stranger}


def url_for(name, world):
    """The route with the real workspace and event, and an unused id for every other part."""
    kwargs = {}
    for kind, part in ft.System().converters(name):
        kwargs[part] = {
            "workspace_public_id": world["workspace"].public_id,
            "event_public_id": world["event"].public_id,
        }.get(part, uuid.uuid4() if kind == "uuid" else "x")
    return reverse(name, kwargs=kwargs)


def claimed_routes():
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        for ref in feature.claims["authorization"].refs:
            if ref.startswith("route:"):
                yield feature.key, ref.partition(":")[2]


def matrix_for(name):
    system = ft.System()
    pattern = system.routes()[name]
    return [r for r in system.permission_matrix() if r["path"] == pattern]


def send(client, method, url):
    return client.generic(method, url, data=json.dumps({}), content_type="application/json")


def test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller(world):
    checked = 0
    for key, name in claimed_routes():
        for row in matrix_for(name):
            assert row["access"] == "roles", f"{key}/{name} {row['method']} is open to more"
            allowed = {str(r.value if hasattr(r, "value") else r) for r in row["roles"]}
            url = url_for(name, world)
            for role, user in world["people"].items():
                if role not in allowed:
                    got = send(client_for(user), row["method"], url).status_code
                    assert got in (403, 404), f"{key}/{name} {row['method']} as {role}: {got}"
                    checked += 1
            for who, client in (
                ("a stranger", client_for(world["stranger"])),
                ("a signed-out caller", client_for()),
            ):
                got = send(client, row["method"], url).status_code
                assert got in (401, 403, 404), f"{key}/{name} {row['method']} as {who}: {got}"
                checked += 1
    assert checked > 100


def test_a_signed_in_caller_of_the_wrong_role_learns_nothing_from_the_refusal(world):
    """A refusal never carries the record: the body is the same whatever the id."""
    name = "stage-detail"
    participant = client_for(world["people"][Role.PARTICIPANT.value])
    unknown = participant.delete(url_for(name, world))
    stage = Stage.objects.create(event=world["event"], name="Build")
    real = participant.delete(
        reverse(
            name,
            kwargs={
                "workspace_public_id": world["workspace"].public_id,
                "event_public_id": world["event"].public_id,
                "stage_public_id": stage.public_id,
            },
        )
    )
    assert unknown.status_code == real.status_code in (403, 404)
    assert unknown.json() == real.json()
    assert Stage.objects.filter(pk=stage.pk).exists()


def projects_world(world):
    owner = world["people"][Role.PARTICIPANT.value]
    other = User.objects.create_user(username="other-participant", password="unused")
    Membership.objects.create(user=other, workspace=world["workspace"], role=Role.PARTICIPANT)
    base = f"/api/v1/workspaces/{world['workspace'].public_id}/events/{world['event'].public_id}/"
    created = client_for(owner).post(
        base + "projects/", {"name": "Mine"}, content_type="application/json"
    )
    assert created.status_code == 201
    project = Project.objects.get(public_id=created.json()["public_id"])
    stage = Stage.objects.create(event=world["event"], name="Build")
    return {"owner": owner, "other": other, "project": project, "stage": stage, "base": base}


def test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it(world):
    p = projects_world(world)
    kwargs = {
        "workspace_public_id": world["workspace"].public_id,
        "event_public_id": world["event"].public_id,
        "project_public_id": p["project"].public_id,
        "stage_public_id": p["stage"].public_id,
    }

    def route(name):
        wanted = {part for _, part in ft.System().converters(name)}
        return reverse(name, kwargs={k: v for k, v in kwargs.items() if k in wanted})

    project_url = route("project-detail")
    names = (
        "project-detail",
        "project-members",
        "submission-detail",
        "submission-finalize",
        "artifact-list",
        "artifact-upload-intent",
    )
    # every writing method each of these routes really has, from the matrix itself
    paths = {
        route(name): [r["method"] for r in matrix_for(name) if r["method"] in WRITES]
        for name in names
    }
    assert all(paths.values())
    before = (Project.objects.count(), ProjectMembership.objects.count())
    for url, methods in paths.items():
        for method in methods:
            got = send(client_for(p["other"]), method, url).status_code
            assert got in (403, 404), f"{method} {url}: {got}"
    assert (Project.objects.count(), ProjectMembership.objects.count()) == before
    p["project"].refresh_from_db()
    assert p["project"].name == "Mine"
    assert not p["project"].submissions.exists()
    # the same member of the same workspace is refused reading it, too
    assert client_for(p["other"]).get(project_url).status_code == 404
    # whereas its owner is allowed
    assert client_for(p["owner"]).get(project_url).status_code == 200


def test_objects_of_another_workspace_or_event_are_not_found(world):
    p = projects_world(world)
    elsewhere = Workspace.objects.create(name="Elsewhere", slug="elsewhere")
    Membership.objects.create(
        user=p["owner"], workspace=elsewhere, role=Role.ORGANIZER
    )  # an organizer there, a participant here
    foreign_event = Event.objects.create(workspace=elsewhere, name="Foreign", slug="foreign")
    organizer = client_for(p["owner"])
    here = f"/api/v1/workspaces/{world['workspace'].public_id}/events/{world['event'].public_id}/"
    other_event = f"/api/v1/workspaces/{elsewhere.public_id}/events/{foreign_event.public_id}/"
    tail = f"projects/{p['project'].public_id}/"
    # the project through a workspace and event it does not belong to
    assert organizer.get(other_event + tail).status_code == 404
    assert (
        organizer.patch(other_event + tail, {}, content_type="application/json").status_code == 404
    )
    # an organizer elsewhere has no standing in this workspace
    stage = Stage.objects.create(event=foreign_event, name="Elsewhere stage")
    got = organizer.patch(
        here + f"stages/{stage.public_id}/", {"name": "Hijacked"}, content_type="application/json"
    )
    assert got.status_code in (403, 404)
    stage.refresh_from_db()
    assert stage.name == "Elsewhere stage"
    # a stage of another event is not reachable through this one
    boss = client_for(world["people"][Role.ORGANIZER.value])
    got = boss.patch(
        here + f"stages/{stage.public_id}/", {"name": "Hijacked"}, content_type="application/json"
    )
    assert got.status_code == 404
    stage.refresh_from_db()
    assert stage.name == "Elsewhere stage"
