"""PD-F003-B01-T06: the REST claims of the completeness contract, held against real responses.

The verifier reads the OpenAPI document; these tests send the requests. Every list a feature claims
returns an array of what its schema describes, every claimed detail returns one record with a
public id, and every refusal of every claimed route is JSON in the shared error shape (`detail`,
field messages or a list of messages), never an empty or HTML body."""

import json
import uuid

import pytest
from core import features as ft
from core import features_rest
from django.urls import reverse

from tests.integration import test_feature_audit as harness

pytestmark = pytest.mark.django_db

world = harness.world  # the same people, event and project the audit proof uses
scenarios, client_for, where = harness.scenarios, harness.client_for, harness.where


def claimed(kind):
    found = []
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        got, _, _ = features_rest.parse(feature.claims["rest"])
        found += [(feature.key, route) for route in got.get(kind, [])]
    return found


LISTS, DETAILS = claimed("list"), claimed("detail")
WRITES = harness.DECLARED


def call(world, who, route, method, kwargs, body=None):
    wanted = {part for _, part in ft.System().converters(route)}
    url = reverse(route, kwargs={k: v for k, v in kwargs.items() if k in wanted})
    clients = world.setdefault("clients", {})
    clients.setdefault(who, client_for(world["people"][who]))
    return clients[who].generic(
        method, url, json.dumps(body) if body is not None else "", content_type="application/json"
    )


def is_shared_error(response) -> bool:
    """`detail`, field messages, or a list of messages, as JSON."""
    if "json" not in response.headers.get("Content-Type", ""):
        return False
    try:
        body = response.json()
    except ValueError:
        return False
    if isinstance(body, list):
        return bool(body) and all(isinstance(item, (str, dict)) for item in body)
    return isinstance(body, dict) and bool(body)


# --- refusals ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "route", "method", "action"),
    WRITES,
    ids=[f"{k}:{r}:{m}" for k, r, m, _ in WRITES],
)
def test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape(
    world, key, route, method, action
):
    who, kwargs, body = scenarios(world)[(route, method)]()
    world["people"]["intruder"] = harness.user("intruder")
    refused = call(world, "intruder", route, method, kwargs, body)  # a stranger to the workspace
    assert refused.status_code in (401, 403, 404)
    assert is_shared_error(refused), (route, method, refused.status_code, refused.content[:200])
    signed_out = harness.Client().generic(
        method,
        reverse(
            route,
            kwargs={
                k: v
                for k, v in kwargs.items()
                if k in {p for _, p in ft.System().converters(route)}
            },
        ),
        json.dumps(body) if body is not None else "",
        content_type="application/json",
    )
    assert signed_out.status_code in (401, 403)
    assert is_shared_error(signed_out)
    # an invalid or unknown thing is refused in the same shape when it is refused at all
    odd = call(
        world,
        who,
        route,
        method,
        {
            **kwargs,
            **{
                k: uuid.uuid4()
                for k in kwargs
                if k.endswith("_public_id") and k not in ("workspace_public_id", "event_public_id")
            },
        },
        body,
    )
    if odd.status_code >= 400:
        assert is_shared_error(odd), (route, method, odd.status_code, odd.content[:200])


def test_an_invalid_body_is_refused_with_keyed_messages(world):
    cases = [
        ("track-list", {"name": ""}, "name"),
        ("stage-list", {"name": ""}, "name"),
        ("form-list", {"name": ""}, "name"),
        ("announcement-list", {"title": "", "body": ""}, "title"),
    ]
    for route, body, field in cases:
        response = call(world, "organizer", route, "POST", where(world), body)
        assert response.status_code == 400 and is_shared_error(response)
        assert field in response.json()


def test_a_member_who_may_not_see_a_project_gets_a_json_404_not_an_empty_one(world):
    project = world["project"]
    kwargs = where(world, project_public_id=project.public_id)
    for route, method in (("project-detail", "GET"), ("project-detail", "PATCH")):
        response = call(world, "bob", route, method, kwargs, {})
        assert response.status_code == 404 and is_shared_error(response)
        assert response.json() == {"detail": "Not found."}


# --- lists and details ---------------------------------------------------------------------------


def seed(world, route):
    """Who reads the list and with what ids, after something exists to list."""
    table = {
        "event-list": ("event-list", "POST"),
        "track-list": ("track-list", "POST"),
        "announcement-list": ("announcement-list", "POST"),
        "event-application-list": ("event-application-decide", "POST"),
        "webhook-list": ("webhook-list", "POST"),
        "award-list": ("award-list", "POST"),
        "stage-list": ("stage-list", "POST"),
        "policy-list": ("policy-list", "POST"),
        "form-list": ("form-list", "POST"),
        "evaluation-plan-list": ("evaluation-plan-list", "POST"),
        "message-list-create": ("message-list-create", "POST"),
        "project-list": ("project-list", "POST"),
        "artifact-list": ("artifact-list", "POST"),
        "my-team-invite-list": ("my-team-invite-list", "POST"),
    }
    key = table.get(route)
    if key is None:  # submission-stage-list: the project and stage exist already
        project, stage = world["project"], world["stage"]
        return "alice", where(
            world, project_public_id=project.public_id, stage_public_id=stage.public_id
        )
    who, kwargs, body = scenarios(world)[key]()
    if key[0] != "event-application-decide":  # an applicant is only made, then listed
        sent = call(world, who, key[0], key[1], kwargs, body)
        assert sent.status_code in (200, 201), (route, sent.content[:200])
    return who, kwargs


@pytest.mark.parametrize(("key", "route"), LISTS, ids=[f"{k}:{r}" for k, r in LISTS])
def test_every_claimed_list_returns_what_its_schema_says(world, key, route):
    system = ft.System()
    who, kwargs = seed(world, route)
    response = call(world, who, route, "GET", kwargs)
    assert response.status_code == 200, (route, response.content[:200])
    rows = response.json()
    assert isinstance(rows, list) and rows, f"{route} did not list what was made"
    op = system.operation(route, "GET")
    schema = system.openapi()["components"]["schemas"][
        op["responses"]["200"]["content"]["application/json"]["schema"]["items"]["$ref"].rsplit(
            "/", 1
        )[-1]
    ]
    properties = set(schema.get("properties", {}))
    for row in rows:
        assert isinstance(row, dict)
        assert set(schema.get("required", [])) <= set(row), (
            route,
            set(schema["required"]) - set(row),
        )
        if properties:
            assert set(row) <= properties, (route, sorted(set(row) - properties))
        if "public_id" in row:
            uuid.UUID(
                str(row["public_id"])
            )  # records are addressed by public id, never by a counter


@pytest.mark.parametrize(("key", "route"), DETAILS, ids=[f"{k}:{r}" for k, r in DETAILS])
def test_every_claimed_detail_returns_one_record_with_a_public_id(world, key, route):
    system = ft.System()
    start = {
        "event-detail": ("event-detail", "PATCH"),
        "artifact-detail": ("artifact-validate", "POST"),
        "evaluation-plan-detail": ("evaluation-plan-detail", "PATCH"),
        "form-detail": ("form-detail", "PUT"),
        "project-detail": ("project-detail", "PATCH"),
        "submission-detail": ("submission-detail", "PUT"),
        "my-team": ("my-team-leave", "POST"),
    }[route]
    who, kwargs, body = scenarios(world)[start]()
    if route == "submission-detail":  # a submission exists once a draft has been saved
        assert call(world, who, start[0], start[1], kwargs, body).status_code == 200
    if route == "my-team":
        who = "bob"
    response = call(world, who, route, "GET", kwargs)
    assert response.status_code == 200, (route, response.content[:200])
    row = response.json()
    assert isinstance(row, dict)
    op = system.operation(route, "GET")
    name = op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[
        -1
    ]
    properties = set(system.schema(name).get("properties", {}))
    if properties:
        assert set(row) <= properties, (route, sorted(set(row) - properties))
    record = row.get("team", row) if route == "my-team" else row
    uuid.UUID(str(record["public_id"]))
