import pytest
from accounts.models import Session, User
from awards.models import PrizeFulfillment
from django.test import Client
from events.models import Event
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def fixture():
    organizer = User.objects.create_user(username="organizer")
    sponsor = User.objects.create_user(username="sponsor")
    other_sponsor = User.objects.create_user(username="other-sponsor")
    participant = User.objects.create_user(username="participant")
    workspace = Workspace.objects.create(name="Awards", slug="awards")
    for user, role in [
        (organizer, Role.ORGANIZER),
        (sponsor, Role.SPONSOR),
        (other_sponsor, Role.SPONSOR),
        (participant, Role.PARTICIPANT),
    ]:
        Membership.objects.create(user=user, workspace=workspace, role=role)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    project = Project.objects.create(event=event, created_by=organizer, name="Project")
    return workspace, event, project, organizer, sponsor, other_sponsor, participant


def awards_base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/awards/"


def portal_base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/sponsor-portal/"


def _create_award_with_winner(organizer_client, workspace, event, project):
    url = awards_base(workspace, event)
    created = organizer_client.post(
        url,
        {
            "name": "Best project",
            "selection_source": "manual",
            "winner_count": 1,
            "require_finalized_submission": False,
        },
        content_type="application/json",
    )
    award_id = created.json()["public_id"]
    organizer_client.post(
        url + f"{award_id}/components/",
        {"kind": "cash", "name": "Cash", "quantity": 1, "amount": "100.00", "currency": "USD"},
        content_type="application/json",
    )
    organizer_client.post(
        url + f"{award_id}/winners/",
        {"project": str(project.public_id)},
        content_type="application/json",
    )
    return award_id


def test_sponsor_sees_only_awards_they_are_tagged_on():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    organizer_client = client_for(organizer)
    award_id = _create_award_with_winner(organizer_client, workspace, event, project)

    assert (
        organizer_client.put(
            awards_base(workspace, event) + f"{award_id}/sponsors/{sponsor.public_id}/"
        ).status_code
        == 201
    )

    list_url = portal_base(workspace, event) + "awards/"
    assert client_for(participant).get(list_url).status_code == 403
    assert client_for(other_sponsor).get(list_url).json() == []

    seen = client_for(sponsor).get(list_url).json()
    assert len(seen) == 1
    assert seen[0]["name"] == "Best project"
    assert seen[0]["eligible_projects"] == [
        {"public_id": str(project.public_id), "name": "Project"}
    ]
    assert seen[0]["judges"] == []
    assert seen[0]["winners"][0]["project_name"] == "Project"

    assert len(organizer_client.get(list_url).json()) == 1


def test_sponsor_can_advance_fulfillment_only_for_their_own_award():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    organizer_client = client_for(organizer)
    award_id = _create_award_with_winner(organizer_client, workspace, event, project)
    organizer_client.put(
        awards_base(workspace, event) + f"{award_id}/sponsors/{sponsor.public_id}/"
    )
    fulfillment = PrizeFulfillment.objects.get()
    transition_url = portal_base(workspace, event) + f"fulfillments/{fulfillment.public_id}/"

    assert (
        client_for(other_sponsor)
        .patch(transition_url, {"state": "contacted"}, content_type="application/json")
        .status_code
        == 403
    )

    advanced = client_for(sponsor).patch(
        transition_url, {"state": "contacted"}, content_type="application/json"
    )
    assert advanced.status_code == 200
    assert advanced.json()["state"] == "contacted"

    invalid = client_for(sponsor).patch(
        transition_url, {"state": "claimed"}, content_type="application/json"
    )
    assert invalid.status_code == 400


def test_removing_a_sponsor_revokes_portal_access():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    organizer_client = client_for(organizer)
    award_id = _create_award_with_winner(organizer_client, workspace, event, project)
    sponsor_url = awards_base(workspace, event) + f"{award_id}/sponsors/{sponsor.public_id}/"
    organizer_client.put(sponsor_url)
    list_url = portal_base(workspace, event) + "awards/"
    assert len(client_for(sponsor).get(list_url).json()) == 1

    assert organizer_client.delete(sponsor_url).status_code == 200
    assert client_for(sponsor).get(list_url).json() == []
