"""PD-F001-B01-T90: cross-cutting proofs for the base-experience slice (T01-T08).

Each capability has its own focused tests; this file covers what cuts across them: authorization
and tenancy of every endpoint the slice added, events that predate it, concurrency on the shared
rows, and failed creation leaving nothing behind.
"""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from eventconfig import services
from eventconfig.models import EventModuleSetting, EventProfile
from events.models import Event
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def world():
    users = {
        name: User.objects.create_user(username=name, password="unused")
        for name in ("org", "admin", "judge", "part", "stranger")
    }
    workspace = Workspace.objects.create(name="Base", slug="base")
    other = Workspace.objects.create(name="Other", slug="other")
    for name, role in (
        ("org", Role.ORGANIZER),
        ("admin", Role.ADMIN),
        ("judge", Role.JUDGE),
        ("part", Role.PARTICIPANT),
    ):
        Membership.objects.create(user=users[name], workspace=workspace, role=role)
    Membership.objects.create(user=users["stranger"], workspace=other, role=Role.ORGANIZER)
    clients = {name: client_for(user) for name, user in users.items()}
    root = f"/api/v1/workspaces/{workspace.public_id}/"
    made = clients["org"].post(
        root + "event-templates/library/hackathon/instantiate/",
        data={"name": "Base"},
        content_type="application/json",
    )
    assert made.status_code == 201, made.content
    return workspace, other, Event.objects.get(workspace=workspace), clients, root


def blind_to_the_race(monkeypatch):
    """Validation ran before the other request committed: only the database constraint sees it."""
    monkeypatch.setattr(Event, "validate_unique", lambda self, exclude=None: None)
    monkeypatch.setattr(Event, "validate_constraints", lambda self, exclude=None: None)


READS = ["configuration/", "workflow/", "readiness/"]


@pytest.mark.parametrize("path", READS)
def test_every_read_is_organizer_or_admin_only_and_tenant_scoped(path):
    workspace, other, event, clients, root = world()
    url = root + f"events/{event.public_id}/{path}"
    for name in ("org", "admin"):
        assert clients[name].get(url).status_code == 200, (name, path)
    for name in ("judge", "part", "stranger"):
        assert clients[name].get(url).status_code == 403, (name, path)
    assert Client().get(url).status_code in (401, 403)
    # An organizer of another workspace cannot reach it by naming their own workspace either.
    cross = f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/{path}"
    assert clients["stranger"].get(cross).status_code == 404


def test_module_changes_and_creation_are_organizer_only():
    workspace, other, event, clients, root = world()
    module = root + f"events/{event.public_id}/modules/mentorship/"
    body = {"enabled": True}
    for name in ("judge", "part", "stranger"):
        denied = clients[name].patch(module, data=body, content_type="application/json")
        assert denied.status_code == 403, name
    assert not EventModuleSetting.objects.filter(event=event).exists()
    create = root + "event-templates/library/hackathon/instantiate/"
    for name in ("judge", "part", "stranger"):
        denied = clients[name].post(create, data={"name": "x"}, content_type="application/json")
        assert denied.status_code == 403, name
    assert Event.objects.filter(workspace=workspace).count() == 1


def test_an_event_that_predates_the_slice_answers_every_endpoint_without_a_profile():
    workspace, _, _, clients, root = world()
    legacy = Event.objects.create(workspace=workspace, name="Legacy", slug="legacy")
    Stage.objects.create(event=legacy, name="Only", is_initial=True)
    assert not EventProfile.objects.filter(event=legacy).exists()
    base = root + f"events/{legacy.public_id}/"
    org = clients["org"]
    configuration = org.get(base + "configuration/")
    assert configuration.status_code == 200 and configuration.json()["preset"] is None
    workflow = org.get(base + "workflow/").json()
    assert (workflow["source"], workflow["preset"], workflow["differences"]) == ("none", None, [])
    assert org.get(base + "readiness/").status_code == 200
    modules = org.get(root + f"modules/?event={legacy.public_id}")
    assert modules.status_code == 200
    # Reading never creates configuration rows for the old event.
    assert not EventProfile.objects.filter(event=legacy).exists()
    assert not EventModuleSetting.objects.filter(event=legacy).exists()


def test_repeating_a_module_change_is_idempotent_and_keeps_one_row():
    workspace, _, event, clients, root = world()
    url = root + f"events/{event.public_id}/modules/mentorship/"
    for _ in range(3):
        response = clients["org"].patch(
            url, data={"enabled": True}, content_type="application/json"
        )
        assert response.status_code == 200, response.content
    assert EventModuleSetting.objects.filter(event=event, module="mentorship").count() == 1


def test_losing_the_race_for_a_derived_address_picks_the_next_free_one(monkeypatch):
    workspace, _, _, clients, root = world()
    # The address was free when derived, but taken before the row was written.
    Event.objects.create(workspace=workspace, name="Racer", slug="racer")
    answers = iter(["racer", "racer-2"])
    monkeypatch.setattr(services, "derive_event_slug", lambda *_: next(answers))
    blind_to_the_race(monkeypatch)
    response = clients["org"].post(
        root + "event-templates/library/hackathon/instantiate/",
        data={"name": "Racer"},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    assert response.json()["slug"] == "racer-2"
    assert Event.objects.filter(workspace=workspace, slug="racer").count() == 1


def test_losing_the_race_for_a_chosen_address_is_a_clear_refusal_that_leaves_nothing(monkeypatch):
    workspace, _, _, clients, root = world()
    Event.objects.create(workspace=workspace, name="Racer", slug="racer")
    blind_to_the_race(monkeypatch)
    events, audits, profiles = (
        Event.objects.count(),
        AuditEvent.objects.count(),
        EventProfile.objects.count(),
    )
    response = clients["org"].post(
        root + "event-templates/library/hackathon/instantiate/",
        data={"name": "Racer", "slug": "racer"},
        content_type="application/json",
    )
    assert response.status_code == 400 and "address" in str(response.json()).lower()
    assert (Event.objects.count(), AuditEvent.objects.count(), EventProfile.objects.count()) == (
        events,
        audits,
        profiles,
    )
