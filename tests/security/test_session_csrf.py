from datetime import timedelta

import pytest
from accounts.models import LoginFailure, Session, User
from community.abuse import client_identifier
from django.test import Client, RequestFactory
from django.utils import timezone
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
JSON = "application/json"


def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    organizer = User.objects.create_user(username="org", password="correct horse")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    return workspace, event, organizer


def create_track(client, workspace, event, **headers):
    return client.post(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/tracks/",
        {"name": "T"},
        content_type=JSON,
        **headers,
    )


def signed_in(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def test_cookie_writes_from_other_origins_are_refused_but_clients_and_same_origin_work():
    workspace, event, organizer = world()
    client = signed_in(organizer)
    assert (
        create_track(client, workspace, event, HTTP_ORIGIN="https://evil.example").status_code
        == 403
    )
    assert create_track(client, workspace, event, HTTP_ORIGIN="null").status_code == 403
    assert (
        create_track(client, workspace, event, HTTP_SEC_FETCH_SITE="cross-site").status_code == 403
    )
    assert not event.tracks.exists()
    assert (
        create_track(client, workspace, event, HTTP_ORIGIN="http://testserver").status_code == 201
    )
    assert create_track(
        client, workspace, event, HTTP_SEC_FETCH_SITE="same-origin"
    ).status_code in (
        201,
        400,
    )
    other = Client()
    other.cookies["session"] = client.cookies["session"].value
    assert (
        other.get(
            f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/tracks/",
            HTTP_ORIGIN="https://evil.example",
        ).status_code
        == 200
    )


def test_trusted_origins_are_configurable(settings):
    workspace, event, organizer = world()
    settings.CSRF_TRUSTED_ORIGINS = ["https://portal.example"]
    client = signed_in(organizer)
    assert (
        create_track(client, workspace, event, HTTP_ORIGIN="https://portal.example").status_code
        == 201
    )
    assert (
        create_track(client, workspace, event, HTTP_ORIGIN="https://evil.example").status_code
        == 403
    )


def test_bearer_credentials_are_not_subject_to_the_browser_origin_rule():
    workspace, event, organizer = world()
    issued = signed_in(organizer).post(
        f"/api/v1/workspaces/{workspace.public_id}/api-credentials/",
        {"name": "ci", "allowed_actions": ["POST:track-list"]},
        content_type=JSON,
    )
    assert issued.status_code == 201, issued.content
    response = Client().post(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/tracks/",
        {"name": "T"},
        content_type=JSON,
        HTTP_AUTHORIZATION=f"Bearer {issued.json()['token']}",
        HTTP_ORIGIN="https://evil.example",
    )
    assert response.status_code == 201, response.content


def test_login_throttles_guessing_per_account_and_resets_on_success():
    _, _, organizer = world()
    User.objects.create_user(username="bystander", password="another pass")
    client = Client()
    login = lambda name, pw: client.post(  # noqa: E731
        "/api/v1/accounts/login/", {"username": name, "password": pw}, content_type=JSON
    )
    for _ in range(10):
        assert login("org", "wrong").status_code == 401
    locked = login("ORG", "correct horse")
    assert locked.status_code == 429 and locked["Retry-After"] == "900"
    assert login("bystander", "another pass").status_code == 200
    for _ in range(10):
        login("ghost", "x")
    assert login("ghost", "x").status_code == 429
    LoginFailure.objects.filter(username="org").update(
        created_at=timezone.now() - timedelta(hours=1)
    )
    assert login("org", "correct horse").status_code == 200
    assert not LoginFailure.objects.filter(username="org").exists()
    assert login("org", "wrong").status_code == 401
    assert (
        client.post(
            "/api/v1/accounts/login/", {"username": ["x"], "password": 1}, content_type=JSON
        ).status_code
        == 401
    )
    assert client.post("/api/v1/accounts/login/", {}, content_type=JSON).status_code == 401


def test_session_cookie_flags_expiry_and_logout():
    _, _, organizer = world()
    client = Client()
    response = client.post(
        "/api/v1/accounts/login/",
        {"username": "org", "password": "correct horse"},
        content_type=JSON,
    )
    cookie = response.cookies["session"]
    assert (
        cookie["httponly"] and cookie["samesite"] == "Lax" and int(cookie["max-age"]) == 12 * 3600
    )
    assert not cookie["secure"]
    secure = Client().post(
        "/api/v1/accounts/login/",
        {"username": "org", "password": "correct horse"},
        content_type=JSON,
        HTTP_X_FORWARDED_PROTO="https",
    )
    assert secure.cookies["session"]["secure"]
    token = cookie.value
    me = lambda: client.get("/api/v1/accounts/me/")  # noqa: E731
    assert me().status_code == 200
    Session.objects.filter(token=token).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert me().status_code == 401
    session = Session.issue(organizer)
    client.cookies["session"] = session.token
    assert client.post("/api/v1/accounts/logout/").status_code == 204
    assert not Session.objects.filter(token=session.token).exists()
    client.cookies["session"] = session.token
    assert me().status_code == 401
    organizer.is_active = False
    organizer.save()
    client.cookies["session"] = Session.issue(organizer).token
    assert me().status_code == 401


def test_client_identifier_trusts_forwarded_for_only_from_an_internal_proxy():
    factory = RequestFactory()

    def ident(remote, forwarded=None):
        extra = {"REMOTE_ADDR": remote}
        if forwarded is not None:
            extra["HTTP_X_FORWARDED_FOR"] = forwarded
        return client_identifier(factory.get("/", **extra))

    assert ident("172.18.0.5", "203.0.113.9") == "203.0.113.9"
    assert ident("172.18.0.5", "203.0.113.9, 10.0.0.1") == "203.0.113.9"
    assert ident("172.18.0.5", "not-an-ip") == "172.18.0.5"
    assert ident("172.18.0.5") == "172.18.0.5"
    assert ident("8.8.8.8", "203.0.113.9") == "8.8.8.8"
    assert ident("127.0.0.1", "2001:db8::1") == "2001:db8::1"
