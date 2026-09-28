import pytest
from awards.models import AwardResource
from django.core.exceptions import ValidationError
from events.models import Track
from test_sponsor_portal import (
    awards_base,
    client_for,
    fixture,
    portal_base,
)

pytestmark = pytest.mark.django_db


def _create_award(organizer_client, workspace, event, *, track=None, name="Best FinTech Hack"):
    payload = {
        "name": name,
        "selection_source": "manual",
        "winner_count": 1,
        "require_finalized_submission": False,
    }
    if track is not None:
        payload["eligibility_track"] = str(track.public_id)
    created = organizer_client.post(
        awards_base(workspace, event), payload, content_type="application/json"
    )
    assert created.status_code == 201, created.content
    return created.json()["public_id"]


def resources_url(workspace, event, award_id, resource_id=None):
    base = portal_base(workspace, event) + f"awards/{award_id}/resources/"
    return base if resource_id is None else base + f"{resource_id}/"


def challenges_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/challenges/"


def test_organizer_and_own_sponsor_can_manage_resources_but_other_sponsors_cannot():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    organizer_client = client_for(organizer)
    award_id = _create_award(organizer_client, workspace, event)
    organizer_client.put(
        awards_base(workspace, event) + f"{award_id}/sponsors/{sponsor.public_id}/"
    )

    created = client_for(sponsor).post(
        resources_url(workspace, event, award_id),
        {"kind": "api", "title": "Widget API", "url": "https://api.example.com/docs"},
        content_type="application/json",
    )
    assert created.status_code == 201, created.content
    resource_id = created.json()["public_id"]

    denied = client_for(other_sponsor).post(
        resources_url(workspace, event, award_id),
        {"kind": "faq", "title": "FAQ", "body": "Ask us anything"},
        content_type="application/json",
    )
    assert denied.status_code == 403

    updated = client_for(sponsor).patch(
        resources_url(workspace, event, award_id, resource_id),
        {"title": "Widget API v2"},
        content_type="application/json",
    )
    assert updated.status_code == 200 and updated.json()["title"] == "Widget API v2"

    assert (
        client_for(other_sponsor)
        .patch(
            resources_url(workspace, event, award_id, resource_id),
            {"title": "Hijacked"},
            content_type="application/json",
        )
        .status_code
        == 403
    )

    organizer_created = organizer_client.post(
        resources_url(workspace, event, award_id),
        {"kind": "starter_repo", "title": "Starter", "url": "https://github.com/example/starter"},
        content_type="application/json",
    )
    assert organizer_created.status_code == 201

    assert (
        client_for(other_sponsor)
        .delete(resources_url(workspace, event, award_id, resource_id))
        .status_code
        == 403
    )
    assert (
        client_for(sponsor)
        .delete(resources_url(workspace, event, award_id, resource_id))
        .status_code
        == 204
    )
    assert AwardResource.objects.filter(public_id=resource_id).count() == 0


def test_resource_kind_requires_a_url_and_every_resource_needs_content():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    organizer_client = client_for(organizer)
    award_id = _create_award(organizer_client, workspace, event)
    organizer_client.put(
        awards_base(workspace, event) + f"{award_id}/sponsors/{sponsor.public_id}/"
    )

    missing_url = client_for(sponsor).post(
        resources_url(workspace, event, award_id),
        {"kind": "starter_repo", "title": "No URL"},
        content_type="application/json",
    )
    assert missing_url.status_code == 400

    empty = client_for(sponsor).post(
        resources_url(workspace, event, award_id),
        {"kind": "contact", "title": "Nobody"},
        content_type="application/json",
    )
    assert empty.status_code == 400

    ok = client_for(sponsor).post(
        resources_url(workspace, event, award_id),
        {"kind": "contact", "title": "Reach us", "body": "sponsor@example.com"},
        content_type="application/json",
    )
    assert ok.status_code == 201


def test_challenge_list_shows_sponsored_awards_to_participants_without_leaking_internals():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    track = Track.objects.create(event=event, name="FinTech")
    organizer_client = client_for(organizer)
    sponsored_id = _create_award(organizer_client, workspace, event, track=track)
    unsponsored_id = _create_award(organizer_client, workspace, event, name="Unsponsored Hack")
    organizer_client.put(
        awards_base(workspace, event) + f"{sponsored_id}/sponsors/{sponsor.public_id}/"
    )
    organizer_client.post(
        awards_base(workspace, event) + f"{sponsored_id}/components/",
        {"kind": "cash", "name": "Cash", "quantity": 1, "amount": "500.00", "currency": "USD"},
        content_type="application/json",
    )
    client_for(sponsor).post(
        resources_url(workspace, event, sponsored_id),
        {"kind": "faq", "title": "Rules", "body": "Build something great."},
        content_type="application/json",
    )

    seen = client_for(participant).get(challenges_url(workspace, event)).json()
    assert [row["public_id"] for row in seen] == [sponsored_id]
    assert unsponsored_id not in [row["public_id"] for row in seen]
    row = seen[0]
    assert row["eligibility_track"] == str(track.public_id)
    assert row["components"][0]["amount"] == 500.0
    assert row["resources"][0]["body"] == "Build something great."
    assert "sponsor_contacts" not in row and "eligible_projects" not in row and "judges" not in row

    assert client_for(organizer).get(challenges_url(workspace, event)).status_code == 200
    from accounts.models import User

    outsider = User.objects.create_user(username="outsider")
    assert client_for(outsider).get(challenges_url(workspace, event)).status_code == 403


def test_award_resource_model_rejects_url_kind_without_url():
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    organizer_client = client_for(organizer)
    award_id = _create_award(organizer_client, workspace, event)
    from awards.models import Award

    award = Award.objects.get(public_id=award_id)
    resource = AwardResource(award=award, kind="workshop", title="Talk", created_by=organizer)
    with pytest.raises(ValidationError):
        resource.full_clean()
