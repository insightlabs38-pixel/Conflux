"""Every API route, every method: anonymous callers, other tenants' organizers and
malformed bodies must never get data, a write, or a server error.
"""

import re
import uuid

import pytest
from accounts.models import Session, User
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver
from integrations.demo_scenarios import generate_demo_event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
METHODS = ("get", "post", "put", "patch", "delete")
# Routes with no workspace scope that are public on purpose, each justified.
# Open to any caller (or any signed-in user) by design; each is exercised by its own tests.
OPEN_BY_DESIGN = (
    "records/",  # signed record verification is portable and public
    "voting/candidates/",  # audience voting needs no account (token/email modes)
    "voting/status/",
    "voting/votes/",
    "voting/results/",
    "voting/request-email-token/",
)
TENANT_OPEN = ("my-application/",)  # anyone signed in may apply to an event
PUBLIC_ROUTES = {
    "health/",  # liveness probe
    "schema/",  # OpenAPI document
    "accounts/oidc/config/",  # whether SSO is offered; exposes no data
    "gallery/",  # official checker gallery
    "submit/",  # official checker closed-event probe
    "events/<uuid:event_public_id>/gallery/",
    "events/<uuid:event_public_id>/awards/",
    "events/<uuid:event_public_id>/finalists/",
    "events/<uuid:event_public_id>/search/",
    "events/<uuid:event_public_id>/questions/",
    "events/<uuid:event_public_id>/announcements/",
    "events/<uuid:event_public_id>/qa/",
}


def routes(patterns=None, prefix=""):
    for entry in patterns if patterns is not None else get_resolver().url_patterns:
        route = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            yield from routes(entry.url_patterns, route)
        elif isinstance(entry, URLPattern) and route.startswith("api/v1/"):
            yield route[len("api/v1/") :], entry


def handlers(entry):
    view_class = getattr(entry.callback, "view_class", None)
    if view_class is None:
        return []
    return [m for m in METHODS if hasattr(view_class, m)]


def fill(route, values):
    def replace(match):
        default = 1 if match.group(1) == "int:" else uuid.uuid4()
        return str(values.get(match.group(2), default))

    return "/api/v1/" + re.sub(r"<(\w+:)?(\w+)>", replace, route)


@pytest.fixture(scope="module")
def sweep_world(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        event = generate_demo_event(seed=61, participants=4, judges=2)
        workspace = event.workspace
        stage = event.stages.get()
        plan = stage.evaluation_plans.get()
        project = event.projects.first()
        award = event.awards.first()
        organizer = workspace.memberships.get(role=Role.ORGANIZER).user
        participant = workspace.memberships.filter(role=Role.PARTICIPANT).first().user
        judge = workspace.memberships.filter(role=Role.JUDGE).first().user
        other = Workspace.objects.create(name="Other tenant", slug="other-tenant")
        attacker = User.objects.create_user(username="other-organizer", password="x")
        Membership.objects.create(workspace=other, user=attacker, role=Role.ORGANIZER)
        owner_ids = set(project.memberships.values_list("user_id", flat=True))
        bystander = (
            workspace.memberships.filter(role=Role.PARTICIPANT)
            .exclude(user_id__in=owner_ids)
            .first()
            .user
        )
        tokens = {
            name: Session.issue(user).token
            for name, user in (
                ("bystander", bystander),
                ("organizer", organizer),
                ("participant", participant),
                ("judge", judge),
                ("attacker", attacker),
            )
        }
        values = {
            "workspace_public_id": workspace.public_id,
            "event_public_id": event.public_id,
            "stage_public_id": stage.public_id,
            "plan_public_id": plan.public_id,
            "project_public_id": project.public_id,
            "award_public_id": award.public_id,
            "user_public_id": participant.public_id,
        }
        yield tokens, values
        Session.objects.filter(token__in=tokens.values()).delete()


def client_for(tokens, name):
    client = Client(raise_request_exception=False)
    if name:
        client.cookies["session"] = tokens[name]
    return client


def all_cases():
    for route, entry in routes():
        for method in handlers(entry):
            yield pytest.param(route, entry, method, id=f"{method.upper()} {route}")


def call(client, method, path):
    return client.generic(method.upper(), path, data=b"{}", content_type="application/json")


def test_sweep_covers_a_meaningful_route_surface():
    assert sum(len(handlers(entry)) for _, entry in routes()) > 300


def test_anonymous_callers_get_nothing_from_workspace_routes(sweep_world):
    tokens, values = sweep_world
    leaks = []
    for route, entry in routes():
        scoped = "workspace_public_id" in route
        if (not scoped and route in PUBLIC_ROUTES) or any(m in route for m in OPEN_BY_DESIGN):
            continue
        for method in handlers(entry):
            response = call(client_for(tokens, None), method, fill(route, values))
            if response.status_code not in (401, 403, 405) and not (
                not scoped and response.status_code == 404
            ):
                leaks.append((method.upper(), route, response.status_code))
    assert not leaks, "\n".join(map(str, leaks))


def test_other_tenants_organizers_are_refused_everywhere(sweep_world):
    tokens, values = sweep_world
    leaks = []
    for route, entry in routes():
        if "workspace_public_id" not in route or any(
            m in route for m in TENANT_OPEN + OPEN_BY_DESIGN
        ):
            continue
        for method in handlers(entry):
            response = call(client_for(tokens, "attacker"), method, fill(route, values))
            if response.status_code not in (401, 403, 404, 405):
                leaks.append((method.upper(), route, response.status_code))
    assert not leaks, "\n".join(map(str, leaks))


@pytest.mark.parametrize("actor", ["organizer", "judge", "participant"])
def test_no_route_returns_a_server_error_for_empty_bodies(sweep_world, actor):
    tokens, values = sweep_world
    failures = []
    for route, entry in routes():
        for method in handlers(entry):
            response = call(client_for(tokens, actor), method, fill(route, values))
            if response.status_code >= 500:
                failures.append((actor, method.upper(), route, response.status_code))
    assert not failures, "\n".join(map(str, failures))


def test_participants_cannot_reach_another_teams_project_objects(sweep_world):
    tokens, values = sweep_world
    leaks = []
    for route, entry in routes():
        if "project_public_id" not in route or "workspace_public_id" not in route:
            continue
        if route.endswith("/comments/"):  # readable by members per the plan's comment_visibility
            handled = [m for m in handlers(entry) if m != "get"]
        else:
            handled = handlers(entry)
        for method in handled:
            response = call(client_for(tokens, "bystander"), method, fill(route, values))
            if response.status_code < 300 or response.status_code >= 500:
                leaks.append((method.upper(), route, response.status_code))
    assert not leaks, "\n".join(map(str, leaks))


ADVERSARIAL_BODIES = [
    b"null",
    b"[]",
    b'"text"',
    b"12345678901234567890123456789012345678901234567890",
    b'{"name": null, "title": null, "email": null, "project": null, "token": null}',
    b'{"name": ["x"], "position": "NaN", "amount": "1e999", "opens_at": {"a": 1}}',
    b'{"name": "\\u0000\\ud800", "description": "' + b"A" * 70000 + b'"}',
    b'{"terms": {"a": {"b": {"c": {"d": {"e": {}}}}}}, "winners": "x", "document": 5}',
    b"{not json",
    b'{"draft_payload": 1, "responses": "x", "criteria": {}, "apply": "yes", "mode": 9}',
]


@pytest.mark.parametrize("actor", ["organizer", "participant", "judge"])
def test_adversarial_bodies_never_cause_a_server_error(sweep_world, actor):
    tokens, values = sweep_world
    failures = []
    client = client_for(tokens, actor)
    for route, entry in routes():
        for method in handlers(entry):
            if method == "get":
                continue
            for body in ADVERSARIAL_BODIES:
                response = client.generic(
                    method.upper(), fill(route, values), data=body, content_type="application/json"
                )
                if response.status_code >= 500:
                    failures.append((actor, method.upper(), route, body[:30], response.status_code))
    assert not failures, "\n".join(map(str, failures[:20]))


QUERY_FUZZ = (
    "?page=-1&limit=999999999999999999999&q=%00%ff&mode=x&status=%27%22&format=csv"
    "&token=%00&start=not-a-uuid&surface=x&state=x&kind=x&taxonomy=x&term=x&ordering=;drop"
)


@pytest.mark.parametrize("actor", ["organizer", "participant", "judge", None])
def test_hostile_query_strings_never_cause_a_server_error(sweep_world, actor):
    tokens, values = sweep_world
    client = client_for(tokens, actor)
    failures = []
    for route, entry in routes():
        if "get" not in handlers(entry):
            continue
        response = client.get(fill(route, values) + QUERY_FUZZ)
        if response.status_code >= 500:
            failures.append((actor, route, response.status_code))
    assert not failures, "\n".join(map(str, failures))
