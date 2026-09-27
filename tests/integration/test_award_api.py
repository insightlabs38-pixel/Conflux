import pytest
from accounts.models import Session, User
from awards.models import Award, PrizeComponent, PrizeFulfillment
from django.test import Client
from events.models import Event
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    user = User.objects.create_user(username="award-organizer", password="unused")
    workspace = Workspace.objects.create(name="Awards", slug="awards")
    Membership.objects.create(user=user, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event", is_public=True)
    project = Project.objects.create(event=event, created_by=user, name="Project")
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return workspace, event, project, client


def base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/awards/"


def test_organizer_creates_selects_and_publishes_without_leaking_override_evidence():
    workspace, event, project, client = fixture()
    url = base(workspace, event)
    assert Client().get(url).status_code in (401, 403)
    candidates = client.get(url + "candidates/")
    assert candidates.status_code == 200
    assert candidates.json()[0]["public_id"] == str(project.public_id)
    created = client.post(
        url,
        {
            "name": "Best project",
            "selection_source": "manual",
            "winner_count": 1,
            "require_finalized_submission": False,
        },
        content_type="application/json",
    )
    assert created.status_code == 201
    award_id = created.json()["public_id"]
    assert Client().get(f"/api/v1/events/{event.public_id}/awards/").json() == []
    component = client.post(
        url + f"{award_id}/components/",
        {"kind": "cash", "name": "Cash", "quantity": 1, "amount": "100.00", "currency": "USD"},
        content_type="application/json",
    )
    assert component.status_code == 201
    assert PrizeComponent.objects.count() == 1
    selected = client.post(
        url + f"{award_id}/winners/",
        {"project": str(project.public_id), "override_reason": "Internal note"},
        content_type="application/json",
    )
    assert selected.status_code == 201
    fulfillment = PrizeFulfillment.objects.get()
    transition_url = url + f"{award_id}/fulfillments/{fulfillment.public_id}/"
    assert (
        client.patch(transition_url, {"state": "sent"}, content_type="application/json").status_code
        == 400
    )
    for state in ("contacted", "verified", "sent"):
        assert (
            client.patch(
                transition_url, {"state": state}, content_type="application/json"
            ).status_code
            == 200
        )
    assert (
        client.patch(
            transition_url, {"state": "failed"}, content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        client.patch(
            transition_url, {"state": "claimed"}, content_type="application/json"
        ).status_code
        == 200
    )
    assert client.post(url + f"{award_id}/publish/").status_code == 200
    assert Award.objects.get(public_id=award_id).published_at is not None
    public = Client().get(f"/api/v1/events/{event.public_id}/awards/")
    assert public.status_code == 200
    assert public.json()[0]["winners"][0]["project_name"] == "Project"
    assert "Internal note" not in str(public.json())
    assert client.post(url + f"{award_id}/publish/").status_code == 400
    event.is_public = False
    event.save(update_fields=["is_public"])
    assert Client().get(f"/api/v1/events/{event.public_id}/awards/").status_code == 404


def test_candidates_are_scoped_to_event_not_caller_membership():
    workspace, event, _own_project, client = fixture()
    other_user = User.objects.create_user(username="participant", password="unused")
    other_project = Project.objects.create(event=event, created_by=other_user, name="Other Team")
    url = base(workspace, event)
    candidates = client.get(url + "candidates/")
    assert candidates.status_code == 200
    candidate_ids = {item["public_id"] for item in candidates.json()}
    assert str(other_project.public_id) in candidate_ids


def test_cross_event_and_invalid_component_are_rejected():
    workspace, event, project, client = fixture()
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    foreign = Project.objects.create(event=other, created_by=project.created_by, name="Foreign")
    url = base(workspace, event)
    created = client.post(
        url,
        {
            "name": "A",
            "selection_source": "manual",
            "winner_count": 1,
            "require_finalized_submission": False,
        },
        content_type="application/json",
    )
    award_id = created.json()["public_id"]
    assert (
        client.post(
            url + f"{award_id}/winners/",
            {"project": str(foreign.public_id)},
            content_type="application/json",
        ).status_code
        == 404
    )
    bad = client.post(
        url + f"{award_id}/components/",
        {"kind": "service", "name": "Mentorship", "quantity": 1, "amount": "500.00"},
        content_type="application/json",
    )
    assert bad.status_code == 400
    assert PrizeComponent.objects.count() == 0


def test_component_added_after_winner_creates_fulfillment_and_failed_needs_note():
    workspace, event, project, client = fixture()
    url = base(workspace, event)
    created = client.post(
        url,
        {
            "name": "A",
            "selection_source": "manual",
            "winner_count": 1,
            "require_finalized_submission": False,
        },
        content_type="application/json",
    )
    award_id = created.json()["public_id"]
    assert (
        client.post(
            url + f"{award_id}/winners/",
            {"project": str(project.public_id)},
            content_type="application/json",
        ).status_code
        == 201
    )
    assert (
        client.post(
            url + f"{award_id}/components/",
            {"kind": "service", "name": "Mentorship", "quantity": 1},
            content_type="application/json",
        ).status_code
        == 201
    )
    fulfillment = PrizeFulfillment.objects.get()
    transition_url = url + f"{award_id}/fulfillments/{fulfillment.public_id}/"
    for state in ("contacted", "verified", "sent"):
        assert (
            client.patch(
                transition_url, {"state": state}, content_type="application/json"
            ).status_code
            == 200
        )
    assert (
        client.patch(
            transition_url, {"state": "failed", "note": ""}, content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        client.patch(
            transition_url,
            {"state": "failed", "note": "Could not contact winner"},
            content_type="application/json",
        ).status_code
        == 200
    )
