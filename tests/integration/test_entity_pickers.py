"""PD-F004-B05-T05: records an organizer must choose (a team, a person) are listed by name through
the entity query, so no screen needs an id typed in."""

import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from participation.models import Team
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def world():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    outsider = User.objects.create_user(username="out", password="unused")
    workspace = Workspace.objects.create(name="P", slug="p")
    other = Workspace.objects.create(name="Q", slug="q")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=outsider, workspace=other, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    elsewhere = Event.objects.create(workspace=other, name="F", slug="f")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/entities/"
    return event, elsewhere, organizer, judge, base


def test_people_are_this_workspaces_members_listed_once_by_username():
    event, _, organizer, judge, base = world()
    response = client_for(organizer).get(base + "people/", {"columns": "username"})
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [r["username"] for r in rows] == ["jdg", "org"]  # org holds two roles, listed once
    assert {r["id"] for r in rows} == {str(judge.public_id), str(organizer.public_id)}
    assert set(rows[0]) == {"id", "username"}  # no email or other personal field is offered


def test_people_can_be_narrowed_by_typing_part_of_a_name():
    _, _, organizer, _, base = world()
    response = client_for(organizer).get(
        base + "people/",
        {"filter": '{"field":"username","op":"contains","value":"jd"}', "columns": "username"},
    )
    assert [r["username"] for r in response.json()["rows"]] == ["jdg"]


def test_teams_are_this_events_teams_by_name():
    event, elsewhere, organizer, _, base = world()
    mine = Team.objects.create(event=event, name="Zeta")
    Team.objects.create(event=event, name="Alpha")
    Team.objects.create(event=elsewhere, name="Foreign")
    response = client_for(organizer).get(base + "teams/", {"columns": "name"})
    rows = response.json()["rows"]
    assert [r["name"] for r in rows] == ["Alpha", "Zeta"]
    assert str(mine.public_id) in {r["id"] for r in rows}


def test_only_organizers_may_list_people_and_teams():
    _, _, _, judge, base = world()
    for entity in ("people", "teams"):
        assert client_for(judge).get(base + f"{entity}/").status_code == 403
