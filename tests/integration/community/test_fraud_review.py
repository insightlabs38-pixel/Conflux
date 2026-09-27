import pytest
from accounts.models import Session
from audit.models import AuditEvent
from community import abuse
from events.models import Event
from test_voting_flows import open_plan
from test_voting_plan_api import cookie_client, make_fixture, plan_url

pytestmark = pytest.mark.django_db


def review_url(workspace, event, suffix=""):
    return plan_url(workspace, event, f"abuse-signals/{suffix}")


def test_signal_evidence_and_audit_are_event_scoped_and_private():
    workspace, event, organizer, participant = make_fixture()
    plan = open_plan(event, identity_mode="token")
    signal = abuse.record_signal(
        plan, "token_replay_attempt", "A redeemed token was reused.", {"state": "redeemed"}
    )
    client = cookie_client(Session.issue(organizer).token)
    listed = client.get(review_url(workspace, event))
    assert listed.status_code == 200
    assert listed.json()[0]["public_id"] == str(signal.public_id)
    assert listed.json()[0]["evidence"] == {"state": "redeemed"}
    assert "token" not in str(listed.json()[0]["evidence"])
    timeline = client.get(plan_url(workspace, event, "audit/"))
    assert timeline.status_code == 200
    assert any(
        row["detail"] == "Suspicious voting activity: token replay attempt"
        for row in timeline.json()
    )
    assert client.get(review_url(workspace, event)).json()[0]["resolved_at"] is None
    outsider = cookie_client(Session.issue(participant).token)
    assert outsider.get(review_url(workspace, event)).status_code == 403
    assert outsider.get(plan_url(workspace, event, "audit/")).status_code == 403

    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    other_plan = open_plan(other_event, identity_mode="token")
    abuse.record_signal(other_plan, "invalid_token_attempt", "Unknown token.")
    assert len(client.get(review_url(workspace, event)).json()) == 1
    assert len(client.get(review_url(workspace, other_event)).json()) == 1
    assert len(client.get(plan_url(workspace, event, "audit/")).json()) == 1


def test_resolution_requires_note_is_single_use_and_records_actor():
    workspace, event, organizer, participant = make_fixture()
    plan = open_plan(event)
    signal = abuse.record_signal(plan, "duplicate_vote_attempt", "Duplicate ballot.")
    url = review_url(workspace, event, f"{signal.public_id}/resolve/")
    organizer_client = cookie_client(Session.issue(organizer).token)
    participant_client = cookie_client(Session.issue(participant).token)
    assert (
        participant_client.post(
            url, {"resolution_note": "Reviewed"}, content_type="application/json"
        ).status_code
        == 403
    )
    assert (
        organizer_client.post(
            url, {"resolution_note": "  "}, content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        organizer_client.post(
            url, {"resolution_note": "Reviewed"}, content_type="application/json"
        ).status_code
        == 200
    )
    signal.refresh_from_db()
    assert signal.resolved_by == organizer
    assert signal.resolution_note == "Reviewed"
    assert (
        organizer_client.post(
            url, {"resolution_note": "Again"}, content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        AuditEvent.objects.filter(
            action="community_abuse.resolved", target_id=str(signal.public_id)
        ).count()
        == 1
    )


def test_review_cannot_resolve_signal_from_another_event():
    workspace, event, organizer, _ = make_fixture()
    open_plan(event)
    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    other_signal = abuse.record_signal(
        open_plan(other_event), "invalid_token_attempt", "Unknown token."
    )
    client = cookie_client(Session.issue(organizer).token)
    assert (
        client.post(
            review_url(workspace, event, f"{other_signal.public_id}/resolve/"),
            {"resolution_note": "Wrong event"},
            content_type="application/json",
        ).status_code
        == 404
    )
    assert other_signal.resolved_at is None


def test_review_pagination_and_invalid_offset():
    workspace, event, organizer, _ = make_fixture()
    plan = open_plan(event)
    for index in range(3):
        abuse.record_signal(plan, "invalid_token_attempt", f"Attempt {index}.")
    client = cookie_client(Session.issue(organizer).token)
    first = client.get(review_url(workspace, event) + "?offset=0").json()
    second = client.get(review_url(workspace, event) + "?offset=2").json()
    assert len(first) == 3
    assert len(second) == 1
    assert second[0]["public_id"] == first[2]["public_id"]
    assert len(client.get(plan_url(workspace, event, "audit/?offset=2")).json()) == 1
    assert client.get(review_url(workspace, event) + "?offset=-1").status_code == 400
    assert client.get(plan_url(workspace, event, "audit/?offset=oops")).status_code == 400
