"""PD-F005-B02-T02: an organizer's own recent actions, from the existing workspace audit log.

`mine` limits the log to what the caller did and `limit` bounds it; without them the endpoint
answers exactly what it always did."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def world():
    ada = User.objects.create_user(username="ada", password="unused")
    ben = User.objects.create_user(username="ben", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="W", slug="w")
    for user, role in ((ada, Role.ORGANIZER), (ben, Role.ADMIN), (judge, Role.JUDGE)):
        Membership.objects.create(user=user, workspace=workspace, role=role)
    for index in range(5):
        AuditEvent.objects.create(workspace=workspace, actor=ada, action=f"ada.{index}")
        AuditEvent.objects.create(workspace=workspace, actor=ben, action=f"ben.{index}")
    AuditEvent.objects.create(workspace=workspace, actor=None, action="system.tick")
    return workspace, ada, ben, judge, f"/api/v1/audit/{workspace.public_id}/"


def test_without_parameters_the_log_is_what_it_always_was():
    _, ada, _, _, url = world()
    rows = client_for(ada).get(url).json()
    assert len(rows) == 11
    assert {r["actor"] for r in rows} == {"ada", "ben", None}


def test_mine_is_only_the_callers_own_actions_newest_first():
    _, ada, ben, _, url = world()
    rows = client_for(ada).get(url, {"mine": "1"}).json()
    assert [r["action"] for r in rows] == ["ada.4", "ada.3", "ada.2", "ada.1", "ada.0"]
    assert {r["actor"] for r in rows} == {"ada"}
    theirs = client_for(ben).get(url, {"mine": "true"}).json()
    assert {r["actor"] for r in theirs} == {"ben"}


def test_limit_bounds_the_answer_and_refuses_nonsense():
    _, ada, _, _, url = world()
    client = client_for(ada)
    assert len(client.get(url, {"mine": "1", "limit": "2"}).json()) == 2
    assert [r["action"] for r in client.get(url, {"limit": "1"}).json()] == ["system.tick"]
    for bad in ("0", "201", "-1", "many"):
        response = client.get(url, {"limit": bad})
        assert response.status_code == 400, bad
        assert "limit" in response.json()


def test_only_organizers_and_admins_may_read_it():
    _, _, _, judge, url = world()
    assert client_for(judge).get(url, {"mine": "1"}).status_code == 403
    assert Client().get(url, {"mine": "1"}).status_code in (401, 403)
