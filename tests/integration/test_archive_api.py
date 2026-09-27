import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    user = User.objects.create_user(username="archive-organizer", password="unused")
    workspace = Workspace.objects.create(name="Archives", slug="archives")
    Membership.objects.create(user=user, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return workspace, event, client


def test_export_requires_organizer_role():
    _workspace, event, _client = fixture()
    url = f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/archive/"
    assert Client().get(url).status_code in (401, 403)


def test_export_default_mode_omits_projects_and_full_includes_the_key():
    workspace, event, client = fixture()
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/archive/"
    config = client.get(url)
    assert config.status_code == 200
    assert config.json()["format_version"] == 1
    assert "projects" not in config.json()
    full = client.get(url, {"mode": "full"})
    assert full.status_code == 200
    assert full.json()["projects"] == []
    assert client.get(url, {"mode": "bogus"}).status_code == 400


def test_import_creates_a_new_event_and_reexports_equivalently():
    workspace, event, client = fixture()
    export_url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/archive/"
    archive = client.get(export_url).json()

    import_url = f"/api/v1/workspaces/{workspace.public_id}/archive/import/"
    created = client.post(
        import_url,
        {"name": "Cloned", "slug": "cloned", "archive": archive},
        content_type="application/json",
    )
    assert created.status_code == 201
    assert created.json()["slug"] == "cloned"
    assert Event.objects.filter(workspace=workspace, slug="cloned").exists()
    assert Event.objects.filter(workspace=workspace).count() == 2


def test_import_surfaces_validation_errors_as_bad_request():
    workspace, _event, client = fixture()
    import_url = f"/api/v1/workspaces/{workspace.public_id}/archive/import/"
    bad = client.post(
        import_url,
        {"name": "X", "slug": "x", "archive": {"mode": "config"}},
        content_type="application/json",
    )
    assert bad.status_code == 400
