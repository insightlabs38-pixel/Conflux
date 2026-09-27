import pytest
from accounts.models import ApiCredential, Session, User
from audit.models import AuditEvent
from django.test import Client
from django.utils import timezone
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    workspace = Workspace.objects.create(name="Main", slug="main")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    first = Event.objects.create(workspace=workspace, name="First", slug="first")
    second = Event.objects.create(workspace=workspace, name="Second", slug="second")
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    return organizer, workspace, first, second, client


def credential_url(workspace):
    return f"/api/v1/workspaces/{workspace.public_id}/api-credentials/"


def bearer(token):
    return Client(HTTP_AUTHORIZATION=f"Bearer {token}")


def test_credential_is_one_time_and_action_scoped():
    organizer, workspace, _, _, session = fixture()
    issued = session.post(
        credential_url(workspace),
        {"name": "Read events", "allowed_actions": ["GET:event-list"]},
        content_type="application/json",
    )
    assert issued.status_code == 201
    token = issued.json()["token"]
    assert token
    assert token not in str(session.get(credential_url(workspace)).json())
    stored = ApiCredential.objects.get(public_id=issued.json()["public_id"])
    assert stored.token_digest != token
    assert token not in str(AuditEvent.objects.filter(action="api_credential.issued").values())
    events_url = f"/api/v1/workspaces/{workspace.public_id}/events/"
    assert bearer(token).get(events_url).status_code == 200
    assert (
        bearer(token)
        .post(events_url, {"name": "Third"}, content_type="application/json")
        .status_code
        == 401
    )
    assert bearer(token).get(credential_url(workspace)).status_code == 401
    assert bearer("invalid").get(events_url).status_code == 401
    mixed = bearer("invalid")
    mixed.cookies["session"] = session.cookies["session"].value
    assert mixed.get(events_url).status_code == 401


def test_event_and_workspace_boundaries_and_revocation():
    organizer, workspace, first, second, session = fixture()
    issued = session.post(
        credential_url(workspace),
        {
            "name": "One event",
            "event": str(first.public_id),
            "allowed_actions": ["GET:event-detail"],
            "expires_in_days": 1,
        },
        content_type="application/json",
    )
    assert issued.status_code == 201
    token = issued.json()["token"]
    first_url = f"/api/v1/workspaces/{workspace.public_id}/events/{first.public_id}/"
    second_url = f"/api/v1/workspaces/{workspace.public_id}/events/{second.public_id}/"
    assert bearer(token).get(first_url).status_code == 200
    assert bearer(token).get(second_url).status_code == 401
    other = Workspace.objects.create(name="Other", slug="other")
    other_event = Event.objects.create(workspace=other, name="Other", slug="other")
    assert (
        bearer(token)
        .get(f"/api/v1/workspaces/{other.public_id}/events/{other_event.public_id}/")
        .status_code
        == 401
    )
    revoke_url = credential_url(workspace) + f"{issued.json()['public_id']}/revoke/"
    assert session.post(revoke_url).status_code == 200
    assert bearer(token).get(first_url).status_code == 401
    assert session.post(revoke_url).status_code == 400


def test_expired_or_unprivileged_owner_cannot_use_credential():
    organizer, workspace, first, _, session = fixture()
    issued = session.post(
        credential_url(workspace),
        {"name": "Read", "allowed_actions": ["GET:event-detail"]},
        content_type="application/json",
    )
    token = issued.json()["token"]
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{first.public_id}/"
    Membership.objects.filter(user=organizer, workspace=workspace).delete()
    assert bearer(token).get(url).status_code == 403
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    credential = ApiCredential.objects.get(public_id=issued.json()["public_id"])
    credential.expires_at = timezone.now()
    credential.save(update_fields=["expires_at"])
    assert bearer(token).get(url).status_code == 401


def test_credential_creation_rejects_invalid_scope_and_wrong_event():
    _, workspace, _, _, session = fixture()
    other = Workspace.objects.create(name="Other", slug="other")
    foreign_event = Event.objects.create(workspace=other, name="Other", slug="other")
    url = credential_url(workspace)
    assert (
        session.post(
            url,
            {"name": "Invalid", "allowed_actions": ["*:*"], "event": str(foreign_event.public_id)},
            content_type="application/json",
        ).status_code
        == 400
    )
    assert (
        session.post(
            url,
            {
                "name": "Wrong event",
                "allowed_actions": ["GET:event-detail"],
                "event": str(foreign_event.public_id),
            },
            content_type="application/json",
        ).status_code
        == 404
    )
    assert ApiCredential.objects.count() == 0
