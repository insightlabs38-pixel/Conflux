"""PD-F003-B01-T05: the idempotency claims of the completeness contract, held against real retries.

Every change a feature accepts declares what happens when the same request arrives again
(`mode:<route>:<METHOD>=<mode>`). This file sends each claimed change twice, as the role that may
make it, and compares what the second send did with the declared mode: `none` and `keyed` (without
a key) repeat the change, every other mode does not. A keyed change runs once for one key."""

import json

import pytest
from audit.models import AuditEvent
from core import features as ft
from core import features_idempotency
from django.apps import apps
from django.urls import reverse

from tests.integration import test_feature_audit as harness

pytestmark = pytest.mark.django_db

world = harness.world  # the same people, event and project the audit proof uses
scenarios, client_for = harness.scenarios, harness.client_for

# Rows written about a change rather than by it: audit trail, stored keys, sessions, evidence.
LOGS = {"audit", "sessions"}
LOG_MODELS = {"core.IdempotencyKey", "artifacts.ArtifactValidation", "accounts.Session"}


def declared():
    found = []
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        modes, _ = features_idempotency.parse(feature.claims["idempotency"])
        found += [
            (feature.key, route, method, mode, detail) for route, method, mode, detail, _ in modes
        ]
    return found


DECLARED = declared()
KEYED = [d for d in DECLARED if d[3] == "keyed"]


def rows():
    """How many rows each data model holds."""
    return {
        model._meta.label: model.objects.count()
        for model in apps.get_models()
        if model._meta.app_label not in LOGS and model._meta.label not in LOG_MODELS
    }


def grown(before, after):
    return sorted(label for label, count in after.items() if count > before.get(label, 0))


def observe(second, before, after):
    if 200 <= second.status_code < 300:
        return "repeated" if grown(before, after) else "same"
    return "refused"


def go(world, route, method, who, kwargs, body, **extra):
    wanted = {part for _, part in ft.System().converters(route)}
    url = reverse(route, kwargs={k: v for k, v in kwargs.items() if k in wanted})
    data = json.dumps(body) if body is not None else ""
    # one client per person, as a real caller keeps one session (a key belongs to its caller)
    clients = world.setdefault("clients", {})
    clients.setdefault(who, client_for(world["people"][who]))
    return clients[who].generic(method, url, data, content_type="application/json", **extra)


def test_every_declared_change_has_a_scenario_and_all_four_unprotected_creates_are_keyed(world):
    assert {(r, m) for _, r, m, _, _ in DECLARED} == set(scenarios(world))
    assert len(DECLARED) == len({(r, m) for _, r, m, _, _ in DECLARED}) >= 40
    assert {r for _, r, _, _, _ in KEYED} == {
        "announcement-list",
        "message-list-create",
        "project-list",
        "artifact-list",
    }
    # what is left unprotected says so, with a reason
    assert {r for _, r, _, m, _ in DECLARED if m == "none"} == {
        "webhook-list",
        "artifact-upload-intent",
        "my-team-invite-list",
    }


@pytest.mark.parametrize(
    ("key", "route", "method", "mode", "detail"),
    DECLARED,
    ids=[f"{k}:{r}:{m}" for k, r, m, _, _ in DECLARED],
)
def test_a_repeated_change_does_what_its_declared_mode_says(
    world, key, route, method, mode, detail
):
    who, kwargs, body = scenarios(world)[(route, method)]()
    first = go(world, route, method, who, kwargs, body)
    assert first.status_code in (200, 201, 204), (route, method, first.content[:300])
    before = rows()
    audits = AuditEvent.objects.count()
    second = go(world, route, method, who, kwargs, body)
    seen = observe(second, before, rows())
    if mode in ("none", "keyed"):
        # nothing stops a second send that carries no key: it is a new change
        assert seen == "repeated", f"{method} {route} ({mode}) did not repeat: {second.status_code}"
        assert AuditEvent.objects.count() > audits
    else:
        assert seen in ("same", "refused"), (
            f"{method} {route} ({mode}) repeated: {grown(before, rows())}"
        )
        if seen == "refused":
            assert second.status_code in (400, 404, 409, 422)  # a refusal, never a server error


@pytest.mark.parametrize(
    ("key", "route", "method", "mode", "detail"),
    KEYED,
    ids=[f"{k}:{r}:{m}" for k, r, m, _, _ in KEYED],
)
def test_a_keyed_change_runs_once_for_one_key_and_a_different_body_is_refused(
    world, key, route, method, mode, detail
):
    who, kwargs, body = scenarios(world)[(route, method)]()
    first = go(world, route, method, who, kwargs, body, HTTP_IDEMPOTENCY_KEY="retry-1")
    assert first.status_code == 201
    before, audits = rows(), AuditEvent.objects.count()
    again = go(world, route, method, who, kwargs, body, HTTP_IDEMPOTENCY_KEY="retry-1")
    assert (again.status_code, again.json()) == (first.status_code, first.json())
    assert grown(before, rows()) == [] and AuditEvent.objects.count() == audits
    changed = (
        {**body, "name": "A different request"}
        if "name" in body
        else {**body, "title": "A different request"}
    )
    clash = go(world, route, method, who, kwargs, changed, HTTP_IDEMPOTENCY_KEY="retry-1")
    assert clash.status_code == 422
    assert grown(before, rows()) == [] and AuditEvent.objects.count() == audits
    fresh = go(world, route, method, who, kwargs, body, HTTP_IDEMPOTENCY_KEY="retry-2")
    assert fresh.status_code == 201 and grown(before, rows())


def test_a_key_belongs_to_its_caller_and_a_failed_change_does_not_keep_it(world):
    who, kwargs, body = scenarios(world)[("project-list", "POST")]()
    one = go(world, "project-list", "POST", who, kwargs, body, HTTP_IDEMPOTENCY_KEY="shared")
    other = go(world, "project-list", "POST", "carol", kwargs, body, HTTP_IDEMPOTENCY_KEY="shared")
    assert one.json()["public_id"] != other.json()["public_id"]  # another caller's key is its own
    refused = go(
        world, "project-list", "POST", who, kwargs, {"name": ""}, HTTP_IDEMPOTENCY_KEY="bad"
    )
    assert refused.status_code == 400
    fixed = go(
        world, "project-list", "POST", who, kwargs, {"name": "Fixed"}, HTTP_IDEMPOTENCY_KEY="bad"
    )
    assert (
        fixed.status_code == 422
    )  # the key was used for a different request, never silently reused


def test_an_unkeyed_retry_of_an_unprotected_change_is_the_documented_repeat(world):
    who, kwargs, body = scenarios(world)[("my-team-invite-list", "POST")]()
    first = go(world, "my-team-invite-list", "POST", who, kwargs, body)
    second = go(world, "my-team-invite-list", "POST", who, kwargs, body)
    assert first.status_code == second.status_code == 201
    assert first.json()["token"] != second.json()["token"]
    for _, route, _, mode, detail in DECLARED:
        if mode == "none":
            assert len(detail) >= features_idempotency.MIN_REASON
