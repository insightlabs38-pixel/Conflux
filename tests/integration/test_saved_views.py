"""PD-F002-B01-T02: saved views store a definition, never rows; viewers keep their own rights."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import entities
from core.models import SavedView
from django.test import Client
from events.models import Event, EventApplication, RegistrationStatus
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def world():
    users = {
        name: User.objects.create_user(username=name, password="unused")
        for name in ("ana", "bo", "admin", "judge", "stranger")
    }
    workspace = Workspace.objects.create(name="V", slug="v")
    for name, role in (
        ("ana", Role.ORGANIZER),
        ("bo", Role.ORGANIZER),
        ("admin", Role.ADMIN),
        ("judge", Role.JUDGE),
    ):
        Membership.objects.create(user=users[name], workspace=workspace, role=role)
    other = Workspace.objects.create(name="O", slug="o")
    Membership.objects.create(user=users["stranger"], workspace=other, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    clients = {name: client_for(user) for name, user in users.items()}
    root = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    return workspace, other, event, users, clients, root


PENDING = {
    "filter": {"field": "status", "op": "eq", "value": "pending"},
    "sort": "-created_at",
    "columns": ["username", "status"],
    "density": "compact",
}


def post(client, root, **body):
    body.setdefault("entity", "applications")
    body.setdefault("name", "Pending")
    body.setdefault("query", PENDING)
    return client.post(root + "views/", data=body, content_type="application/json")


def patch(client, root, view, **body):
    return client.patch(root + f"views/{view}/", data=body, content_type="application/json")


def test_a_view_is_saved_listed_and_run_as_its_definition():
    _, _, event, users, clients, root = world()
    for name, status in (("p1", "pending"), ("p2", "pending"), ("a1", "approved")):
        user = User.objects.create_user(username=name, password="unused")
        EventApplication.objects.create(event=event, user=user, status=status)
    created = post(clients["ana"], root)
    assert created.status_code == 201, created.content
    body = created.json()
    assert body["mine"] is True and body["visibility"] == "private" and body["version"] == 1
    assert body["query"] == PENDING

    listed = clients["ana"].get(root + "views/?entity=applications").json()
    assert [v["name"] for v in listed] == ["Pending"]
    page = clients["ana"].get(root + f"views/{body['public_id']}/run/").json()
    assert page["total"] == 2 and page["density"] == "compact"
    assert page["columns"] == ["username", "status"]
    assert {row["status"] for row in page["rows"]} == {"pending"}
    assert page["view"]["public_id"] == body["public_id"]
    # Paging applies to a run like to any page.
    paged = clients["ana"].get(root + f"views/{body['public_id']}/run/?limit=1&offset=1").json()
    assert paged["total"] == 2 and len(paged["rows"]) == 1
    # The view stores a definition: no rows anywhere in the stored record.
    stored = SavedView.objects.get()
    assert set(stored.query) == {"filter", "sort", "columns", "density"}


def test_defaults_and_validation_happen_at_save_time():
    _, _, _, _, clients, root = world()
    minimal = post(clients["ana"], root, name="All", query={})
    assert minimal.status_code == 201
    assert minimal.json()["query"] == {
        "filter": None,
        "sort": "",
        "columns": [],
        "density": "comfortable",
    }
    bad = [
        ({"query": {"filter": {"field": "nope", "op": "eq", "value": 1}}}, "filter.field"),
        ({"query": {"sort": "nope"}}, "sort"),
        ({"query": {"columns": ["nope"]}}, "columns"),
        ({"query": {"columns": "username"}}, "columns"),
        ({"query": {"density": "tiny"}}, "density"),
        ({"query": {"extra": 1}}, "query"),
        ({"query": "x"}, "query"),
        ({"name": ""}, "name"),
        ({"name": "x" * 81}, "name"),
        ({"entity": "nonsense"}, "entity"),
        ({"visibility": "everyone"}, "visibility"),
    ]
    for body, key in bad:
        response = post(clients["ana"], root, **{"name": "Bad", **body})
        assert response.status_code == 400, (body, response.content)
        assert key in response.json(), (body, response.json())
    assert SavedView.objects.count() == 1


def test_names_are_unique_per_owner_and_there_is_a_quota():
    _, _, event, users, clients, root = world()
    assert post(clients["ana"], root).status_code == 201
    duplicate = post(clients["ana"], root)
    assert duplicate.status_code == 400 and "already have" in str(duplicate.json())
    # Another person may use the same name.
    assert post(clients["bo"], root).status_code == 201
    SavedView.objects.bulk_create(
        SavedView(event=event, owner=users["bo"], entity="projects", name=f"v{i}", query={})
        for i in range(48)
    )
    assert SavedView.objects.filter(owner=users["bo"]).count() == 49
    assert post(clients["bo"], root, name="fiftieth").status_code == 201
    over = post(clients["bo"], root, name="fifty-first")
    assert over.status_code == 400 and "at most 50" in str(over.json())


def test_private_views_belong_to_the_owner_and_organizers_views_are_shared_for_reading():
    _, _, _, users, clients, root = world()
    mine = post(clients["ana"], root).json()["public_id"]
    shared = post(clients["ana"], root, name="Shared", visibility="organizers").json()["public_id"]

    def names(who):
        return sorted(v["name"] for v in clients[who].get(root + "views/").json())

    assert names("ana") == ["Pending", "Shared"]
    assert names("bo") == ["Shared"]
    # A private view is absent (404), not forbidden, for everyone else.
    assert clients["bo"].get(root + f"views/{mine}/").status_code == 404
    assert clients["bo"].get(root + f"views/{mine}/run/").status_code == 404
    assert clients["bo"].get(root + f"views/{shared}/").json()["mine"] is False
    # A viewer can run it, but only the owner can change it.
    assert clients["bo"].get(root + f"views/{shared}/run/").status_code == 200
    assert patch(clients["bo"], root, shared, name="Hijacked").status_code == 403
    assert clients["bo"].delete(root + f"views/{shared}/").status_code == 403
    assert SavedView.objects.filter(name="Shared").exists()
    # A workspace admin may delete someone else's shared view (moderation).
    assert clients["admin"].delete(root + f"views/{shared}/").status_code == 204


def test_sharing_a_view_never_widens_the_rows_anyone_can_see():
    _, _, event, users, clients, root = world()
    user = User.objects.create_user(username="p1", password="unused")
    EventApplication.objects.create(event=event, user=user, status=RegistrationStatus.PENDING)
    shared = post(clients["ana"], root, visibility="organizers").json()["public_id"]
    # A judge cannot query applications, so the shared view does not exist for them.
    assert clients["judge"].get(root + "views/").json() == []
    assert clients["judge"].get(root + f"views/{shared}/").status_code == 404
    assert clients["judge"].get(root + f"views/{shared}/run/").status_code == 404
    # They cannot save one either.
    assert post(clients["judge"], root).status_code == 403
    # The organizer's view yields the same rows as the direct query (rows come from QUERY).
    via_view = clients["bo"].get(root + f"views/{shared}/run/").json()["rows"]
    direct = (
        clients["bo"]
        .get(
            root + "entities/applications/",
            {"filter": '{"field":"status","op":"eq","value":"pending"}', "sort": "-created_at"},
        )
        .json()["rows"]
    )
    assert [r["id"] for r in via_view] == [r["id"] for r in direct]


def test_updates_bump_the_version_refuse_stale_writers_and_are_audited_without_filter_values():
    workspace, _, event, users, clients, root = world()
    created = post(clients["ana"], root).json()
    view = created["public_id"]
    renamed = patch(clients["ana"], root, view, name="Waiting", version=1, visibility="organizers")
    assert renamed.status_code == 200, renamed.content
    assert renamed.json()["version"] == 2 and renamed.json()["visibility"] == "organizers"
    stale = patch(clients["ana"], root, view, name="Again", version=1)
    assert stale.status_code == 409 and stale.json()["code"] == "view_changed"
    assert SavedView.objects.get().name == "Waiting"
    requery = patch(
        clients["ana"],
        root,
        view,
        query={"filter": {"field": "username", "op": "contains", "value": "secret@example.com"}},
        version=2,
    )
    assert requery.status_code == 200 and requery.json()["version"] == 3
    # Keeping the old name after a query change is fine (same owner, same row).
    audits = list(AuditEvent.objects.filter(action__startswith="saved_view.").order_by("id"))
    assert [a.action for a in audits] == [
        "saved_view.created",
        "saved_view.updated",
        "saved_view.updated",
    ]
    assert audits[1].metadata["changes"]
    assert audits[2].metadata["query_changed"] is True
    assert "secret@example.com" not in str([a.metadata for a in audits])


def test_a_definition_that_no_longer_fits_is_reported_not_loosened(monkeypatch):
    _, _, _, _, clients, root = world()
    view = post(clients["ana"], root).json()["public_id"]
    original = entities.get("applications")
    trimmed = entities.Entity(
        original.key,
        original.label,
        original.roles,
        original.base,
        tuple(f for f in original.fields if f.key != "status"),
        original.default_sort,
    )
    monkeypatch.setitem(entities._ENTITIES, "applications", trimmed)
    response = clients["ana"].get(root + f"views/{view}/run/")
    assert response.status_code == 409 and response.json()["code"] == "view_outdated"
    assert "status" in response.json()["detail"]


def test_views_are_scoped_to_their_event_and_workspace_and_deleted_with_it():
    workspace, other, event, users, clients, root = world()
    view = post(clients["ana"], root).json()["public_id"]
    second = Event.objects.create(workspace=workspace, name="E2", slug="e2")
    other_root = f"/api/v1/workspaces/{workspace.public_id}/events/{second.public_id}/"
    assert clients["ana"].get(other_root + "views/").json() == []
    assert clients["ana"].get(other_root + f"views/{view}/").status_code == 404
    cross = f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/views/"
    assert clients["stranger"].get(cross).status_code == 404
    assert clients["stranger"].get(root + "views/").status_code == 403
    assert Client().get(root + "views/").status_code in (401, 403)
    event.delete()
    assert not SavedView.objects.exists()


def test_deleting_a_view_is_audited_and_leaves_the_data():
    _, _, event, users, clients, root = world()
    user = User.objects.create_user(username="p1", password="unused")
    EventApplication.objects.create(event=event, user=user)
    view = post(clients["ana"], root).json()["public_id"]
    assert clients["ana"].delete(root + f"views/{view}/").status_code == 204
    assert clients["ana"].delete(root + f"views/{view}/").status_code == 404
    assert EventApplication.objects.count() == 1
    audit = AuditEvent.objects.get(action="saved_view.deleted")
    assert audit.metadata["name"] == "Pending" and audit.metadata["entity"] == "applications"


def test_a_view_may_carry_a_search_and_older_views_are_unchanged():
    _, _, event, users, clients, root = world()
    for name, note in (("p1", "from Berlin"), ("p2", "from Paris")):
        user = User.objects.create_user(username=name, password="unused")
        EventApplication.objects.create(event=event, user=user, note=note)
    plain = post(clients["ana"], root)
    assert plain.status_code == 201 and "search" not in plain.json()["query"]
    searched = post(
        clients["ana"], root, name="Berlin", query={**PENDING, "filter": None, "search": " berlin "}
    )
    assert searched.status_code == 201, searched.content
    assert searched.json()["query"]["search"] == "berlin"
    page = clients["ana"].get(root + f"views/{searched.json()['public_id']}/run/").json()
    assert page["total"] == 1 and page["search"] == "berlin"
    # a view without search still runs exactly as before
    old = clients["ana"].get(root + f"views/{plain.json()['public_id']}/run/").json()
    assert old["search"] == ""
    # a bad search is refused at save time with the same diagnostics
    bad = post(clients["ana"], root, name="Bad", query={**PENDING, "search": "x"})
    assert bad.status_code == 400
