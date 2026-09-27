import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event, EventStatus, Track
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    owner = User.objects.create_user(username="owner", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="Archive", slug="archive")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(
        workspace=workspace,
        name="Source",
        slug="source",
        status=EventStatus.CLOSED,
        is_public=True,
    )
    Track.objects.create(event=event, name="Hardware")
    Stage.objects.create(event=event, name="Finals", is_initial=True)
    owner_client = Client()
    owner_client.cookies["session"] = Session.issue(owner).token
    judge_client = Client()
    judge_client.cookies["session"] = Session.issue(judge).token
    base = f"/api/v1/workspaces/{workspace.public_id}/"
    archive = owner_client.get(base + f"events/{event.public_id}/archive/").json()
    return workspace, owner_client, judge_client, base, archive


def post_json(client, url, data):
    return client.post(url, data=data, content_type="application/json")


def test_preview_reports_import_diff_and_commits_no_rows():
    workspace, client, _, base, archive = fixture()
    archive["future_section"] = [{"future": True}]
    request = {"name": "Imported", "slug": "imported", "archive": archive}
    response = post_json(client, base + "archive/preview/", request)
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["format_version"] == 1
    assert body["migration_steps"] == []
    assert body["deprecations"] == []
    assert body["ignored_sections"] == ["future_section"]
    changes = {item["field"]: item for item in body["event_changes"]}
    assert changes["name"] == {"field": "name", "source": "Source", "imported": "Imported"}
    assert changes["slug"]["imported"] == "imported"
    assert changes["status"]["imported"] == "draft"
    assert changes["is_public"]["imported"] is False
    sections = {item["section"]: item for item in body["sections"]}
    assert sections["tracks"] == {"section": "tracks", "source_count": 1, "imported_count": 1}
    assert sections["stages"]["imported_count"] == 1
    assert Event.objects.filter(workspace=workspace).count() == 1
    assert Track.objects.filter(event__workspace=workspace).count() == 1
    assert Stage.objects.filter(event__workspace=workspace).count() == 1

    imported = post_json(client, base + "archive/import/", request)
    assert imported.status_code == 201, imported.content
    assert Event.objects.filter(workspace=workspace).count() == 2


def test_preview_rejects_unsupported_version_without_inventing_migration():
    workspace, client, _, base, archive = fixture()
    archive["format_version"] = 0
    response = post_json(
        client,
        base + "archive/preview/",
        {"name": "Imported", "slug": "imported", "archive": archive},
    )
    assert response.status_code == 400
    assert "no migration path" in str(response.json()).lower()
    assert Event.objects.filter(workspace=workspace).count() == 1


def test_full_archive_preview_validates_project_creator_without_persisting_copy():
    workspace, client, _, base, _ = fixture()
    source = Event.objects.get(workspace=workspace)
    Project.objects.create(
        event=source, name="Research prototype", created_by=User.objects.get(username="owner")
    )
    archive = client.get(base + f"events/{source.public_id}/archive/", {"mode": "full"}).json()
    response = post_json(
        client,
        base + "archive/preview/",
        {"name": "Copy", "slug": "copy", "archive": archive},
    )
    assert response.status_code == 200, response.content
    project_section = next(
        section for section in response.json()["sections"] if section["section"] == "projects"
    )
    assert project_section["source_count"] == project_section["imported_count"] == 1
    assert Event.objects.filter(workspace=workspace).count() == 1
    assert Project.objects.count() == 1


def test_config_preview_reports_projects_that_would_be_ignored():
    _, client, _, base, archive = fixture()
    archive["projects"] = [{"name": "Not imported in config mode"}]
    response = post_json(
        client,
        base + "archive/preview/",
        {"name": "Copy", "slug": "copy", "archive": archive},
    )
    assert response.status_code == 200, response.content
    section = next(row for row in response.json()["sections"] if row["section"] == "projects")
    assert section == {"section": "projects", "source_count": 1, "imported_count": 0}


def test_preview_uses_real_import_validation_and_role_boundary():
    workspace, client, judge_client, base, archive = fixture()
    path = base + "archive/preview/"
    request = {"name": "Imported", "slug": "imported", "archive": archive}
    assert post_json(judge_client, path, request).status_code == 403
    assert post_json(Client(), path, request).status_code in (401, 403)
    archive["stage_transitions"] = [
        {"from_ref": "nonexistent", "to_ref": archive["stages"][0]["ref"]}
    ]
    assert post_json(client, path, request).status_code == 400
    assert Event.objects.filter(workspace=workspace).count() == 1
    assert Stage.objects.filter(event__workspace=workspace).count() == 1
    assert (
        post_json(
            client,
            path,
            {
                "name": "Imported",
                "slug": "source",
                "archive": fixture_archive_without_transition(archive),
            },
        ).status_code
        == 400
    )


def fixture_archive_without_transition(archive):
    return {**archive, "stage_transitions": []}
