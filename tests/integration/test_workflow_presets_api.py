import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from stages.models import ParticipationMode, Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    participant = User.objects.create_user(username="member", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    return workspace, event, organizer, participant


def presets_url(workspace, event, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/workflow-presets/{suffix}"
    )


def test_preset_list_advertises_the_two_and_three_round_presets():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)

    body = client.get(presets_url(workspace, event)).json()
    assert body["two_round"]["rounds"] == ["Screening", "Final"]
    assert body["three_round"]["rounds"] == ["Screening", "Semifinal", "Final"]


def test_applying_three_round_creates_a_chained_stage_graph_and_one_plan_each():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)

    response = client.post(
        presets_url(workspace, event, "apply/"),
        {"preset": "three_round"},
        content_type="application/json",
    )
    assert response.status_code == 201
    body = response.json()
    assert [s["name"] for s in body["stages"]] == ["Screening", "Semifinal", "Final"]
    assert [p["name"] for p in body["plans"]] == [
        "Screening judging",
        "Semifinal judging",
        "Final judging",
    ]

    stages = list(Stage.objects.filter(event=event).order_by("position"))
    assert [s.name for s in stages] == ["Screening", "Semifinal", "Final"]
    assert stages[0].is_initial is True
    assert stages[1].is_initial is False and stages[2].is_initial is False
    assert stages[0].participation_mode == ParticipationMode.TEAM_FORMATION
    assert stages[1].participation_mode == ParticipationMode.TEAM_LOCKED
    assert stages[2].participation_mode == ParticipationMode.TEAM_LOCKED
    # Screening -> Semifinal -> Final, chained by StageTransition.
    assert set(stages[0].reaches(target) for target in stages[1:]) == {True}
    assert stages[2].reaches(stages[0]) is False


def test_applying_a_preset_twice_is_rejected_rather_than_silently_merged():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    client.post(
        presets_url(workspace, event, "apply/"),
        {"preset": "two_round"},
        content_type="application/json",
    )

    second = client.post(
        presets_url(workspace, event, "apply/"),
        {"preset": "three_round"},
        content_type="application/json",
    )
    assert second.status_code == 400
    assert Stage.objects.filter(event=event).count() == 2


def test_unknown_preset_is_rejected():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)

    response = client.post(
        presets_url(workspace, event, "apply/"),
        {"preset": "nope"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert Stage.objects.filter(event=event).count() == 0


def test_participant_cannot_apply_a_preset():
    workspace, event, _, participant = make_fixture()
    client = cookie_client(Session.issue(participant).token)

    response = client.post(
        presets_url(workspace, event, "apply/"),
        {"preset": "two_round"},
        content_type="application/json",
    )
    assert response.status_code == 403
    assert Stage.objects.filter(event=event).count() == 0
