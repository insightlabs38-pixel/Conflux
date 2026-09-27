import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from events.models import Event
from integrations.models import EventTemplate
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def test_operator_console_scopes_health_templates_and_activity_to_workspace():
    owner = User.objects.create_user(username="operator", password="unused")
    judge = User.objects.create_user(username="viewer", password="unused")
    workspace = Workspace.objects.create(name="Main", slug="main")
    other = Workspace.objects.create(name="Other", slug="other")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    source = Event.objects.create(workspace=workspace, name="Launch", slug="launch")
    Event.objects.create(workspace=other, name="Private elsewhere", slug="private")
    EventTemplate.objects.create(
        workspace=workspace,
        name="Starter",
        source_event_name="Launch",
        archive={"format_version": 1},
        created_by=owner,
    )
    EventTemplate.objects.create(
        workspace=other,
        name="Other template",
        archive={"format_version": 1},
        created_by=owner,
    )
    AuditEvent.objects.create(workspace=workspace, actor=owner, action="event.updated")
    AuditEvent.objects.create(workspace=other, actor=owner, action="other.secret")
    url = f"/api/v1/workspaces/{workspace.public_id}/operator-console/"
    client = Client()
    client.cookies["session"] = Session.issue(owner).token
    response = client.get(url)
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["event_total"] == 1
    assert body["events"][0]["public_id"] == str(source.public_id)
    assert body["events"][0]["health"] == "blocked"
    assert body["events"][0]["blocker_count"] >= 1
    assert body["template_total"] == 1
    assert [item["name"] for item in body["templates"]] == ["Starter"]
    assert [item["action"] for item in body["activity"]] == ["event.updated"]
    assert body["activity"][0]["actor"] == "operator"

    judge_client = Client()
    judge_client.cookies["session"] = Session.issue(judge).token
    assert judge_client.get(url).status_code == 403
    assert Client().get(url).status_code in (401, 403)
    assert client.get(f"/api/v1/workspaces/{other.public_id}/operator-console/").status_code == 403
