"""PD-F001-B02-T02: destructive and high-impact operations show what they would do, from the domain.

Each preview is checked against what the real endpoint then does, so the answer cannot drift.
"""

from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from django.utils import timezone
from eventconfig.consequences import ACTIONS
from eventconfig.registry import SPECS
from events.models import BasePrize, Event, EventApplication, EventStatus, Track
from projects.models import Project
from stages.models import Stage, StageEntry, StageTransition
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup(key="hackathon", **options):
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Conseq", slug="conseq")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    client = client_for(organizer)
    root = f"/api/v1/workspaces/{workspace.public_id}/"
    made = client.post(
        root + f"event-templates/library/{key}/instantiate/",
        data={"name": "Spring", **options},
        content_type="application/json",
    )
    assert made.status_code == 201, made.content
    event = Event.objects.get(workspace=workspace)
    return (
        workspace,
        organizer,
        client,
        client_for(judge),
        root + f"events/{event.public_id}/",
        event,
    )


def preview(client, base, action, target=None):
    query = f"?action={action}" + (f"&target={target.public_id}" if target else "")
    response = client.get(base + "consequences/" + query)
    assert response.status_code == 200, response.content
    return response.json()


def codes(shown):
    return [c["code"] for c in shown["consequences"]]


def test_a_stage_with_a_published_rubric_is_refused_cleanly_instead_of_failing():
    _, _, client, _, base, event = setup()
    judging = Stage.objects.get(event=event, name="Judging")
    shown = preview(client, base, "stage.delete", judging)
    assert shown["allowed"] is False and shown["refusal"]["code"] == "published_rubric"
    assert "permanent" in shown["refusal"]["message"]
    response = client.delete(base + f"stages/{judging.public_id}/")
    # Was an unhandled ProtectedError (HTTP 500) before the preview reused the same facts.
    assert response.status_code == 400, response.content
    assert response.json()["detail"] == shown["refusal"]["message"]
    assert Stage.objects.filter(pk=judging.pk).exists()


def test_a_stage_delete_says_what_goes_with_it_and_the_audit_records_the_same():
    _, _, client, _, base, event = setup()
    build = Stage.objects.get(event=event, name="Build")
    links = StageTransition.objects.filter(from_stage=build).count()
    shown = preview(client, base, "stage.delete", build)
    assert shown["allowed"] is True and shown["severity"] == "high"
    removed = next(c for c in shown["consequences"] if c["code"] == "removed")
    assert removed["count"] == links == 1 and "stage link" in removed["message"]
    assert client.delete(base + f"stages/{build.public_id}/").status_code == 204
    assert StageTransition.objects.filter(from_stage__event=event).count() == 1
    audit = AuditEvent.objects.get(action="stage.deleted")
    assert {"code": "removed", "count": 1} in audit.metadata["consequences"]


def test_a_stage_that_held_a_participant_is_refused_with_the_endpoints_message():
    _, _, client, _, base, event = setup()
    build = Stage.objects.get(event=event, name="Build")
    StageEntry.objects.create(stage=build, subject_type="project", subject_id="1")
    shown = preview(client, base, "stage.delete", build)
    assert shown["refusal"]["code"] == "has_participants"
    response = client.delete(base + f"stages/{build.public_id}/")
    assert response.status_code == 400
    assert response.json()["detail"] == shown["refusal"]["message"]


def test_a_transition_delete_names_the_advancement_and_a_flow_it_would_break():
    _, _, client, _, base, event = setup()
    stages = {s.name: s for s in Stage.objects.filter(event=event)}
    first = StageTransition.objects.get(from_stage=stages["Build"], to_stage=stages["Judging"])
    shown = preview(client, base, "stage_transition.delete", first)
    assert shown["reversible"] is True and shown["severity"] == "medium"
    assert "Build to Judging" in shown["consequences"][0]["message"]
    assert "graph_invalid" in codes(shown)
    assert "unreachable" in next(
        c["message"] for c in shown["consequences"] if c["code"] == "graph_invalid"
    )
    # A redundant shortcut can go without breaking anything.
    shortcut = StageTransition.objects.create(from_stage=stages["Build"], to_stage=stages["Final"])
    assert "graph_invalid" not in codes(preview(client, base, "stage_transition.delete", shortcut))
    # Previewing never deletes.
    assert StageTransition.objects.filter(pk=first.pk).exists()
    assert client.delete(base + f"stage-transitions/{shortcut.public_id}/").status_code == 204
    assert AuditEvent.objects.filter(action="stage_transition.deleted").count() == 1


def test_a_track_delete_counts_the_projects_that_lose_it():
    workspace, organizer, client, _, base, event = setup()
    track = Track.objects.create(event=event, name="Hardware")
    Project.objects.create(event=event, name="A", created_by=organizer, track=track)
    Project.objects.create(event=event, name="B", created_by=organizer, track=track)
    shown = preview(client, base, "track.delete", track)
    updated = next(c for c in shown["consequences"] if c["code"] == "updated")
    assert updated["count"] == 2 and "2 projects" in updated["message"]
    assert client.delete(base + f"tracks/{track.public_id}/").status_code == 204
    assert Project.objects.filter(event=event, track__isnull=True).count() == 2
    audit = AuditEvent.objects.get(action="track.deleted")
    assert {"code": "updated", "count": 2} in audit.metadata["consequences"]


def test_an_isolated_prize_says_nothing_else_depends_on_it():
    _, _, client, _, base, event = setup()
    prize = BasePrize.objects.create(event=event, name="Grand prize")
    shown = preview(client, base, "base_prize.delete", prize)
    assert codes(shown) == ["isolated"] and shown["allowed"] is True
    assert client.delete(base + f"base-prizes/{prize.public_id}/").status_code == 204


def test_opening_lists_what_is_unresolved_and_the_visibility_outcome():
    _, _, client, _, base, event = setup(
        starts_at=(timezone.now() + timedelta(days=30)).isoformat()
    )
    shown = preview(client, base, "event.open")
    assert shown["allowed"] is True
    unresolved_ids = {c["code"].split(":")[1] for c in shown["consequences"] if ":" in c["code"]}
    assert "judging_pools" in unresolved_ids
    assert (
        "stays private"
        in next(c for c in shown["consequences"] if c["code"] == "visibility")["message"]
    )
    assert "forward_only" in codes(shown)
    event.is_public = True
    event.save(update_fields=["is_public"])
    assert (
        "goes live"
        in next(
            c
            for c in preview(client, base, "event.open")["consequences"]
            if c["code"] == "visibility"
        )["message"]
    )
    # The audit of the real transition records the same unresolved items (the preview's, now).
    unresolved_ids = {
        c["code"].split(":")[1]
        for c in preview(client, base, "event.open")["consequences"]
        if ":" in c["code"]
    }
    assert (
        client.post(
            base + "status/", data={"status": "open"}, content_type="application/json"
        ).status_code
        == 200
    )
    audit = AuditEvent.objects.get(action="event.status_changed")
    recorded = audit.metadata["unresolved"]
    assert set(recorded["blockers"]) | set(recorded["warnings"]) == unresolved_ids


def test_opening_an_event_without_dates_is_refused_with_the_endpoints_reason():
    _, _, client, _, base, _ = setup()
    shown = preview(client, base, "event.open")
    assert shown["allowed"] is False and shown["refusal"]["code"] == "invalid"
    real = client.post(base + "status/", data={"status": "open"}, content_type="application/json")
    assert real.status_code == 400
    assert shown["refusal"]["message"] in str(real.json())


def test_a_status_change_the_endpoint_refuses_is_refused_with_its_message():
    _, _, client, _, base, event = setup()
    shown = preview(client, base, "event.close")  # a draft cannot be closed
    assert shown["allowed"] is False and shown["refusal"]["code"] == "invalid_transition"
    real = client.post(base + "status/", data={"status": "closed"}, content_type="application/json")
    assert real.status_code == 400
    assert real.json()["status"] == shown["refusal"]["message"]

    event.ends_at = timezone.now() - timedelta(days=1)
    event.starts_at = event.ends_at - timedelta(days=1)
    event.save(update_fields=["starts_at", "ends_at"])
    shown = preview(client, base, "event.open")
    assert shown["refusal"]["code"] == "ends_in_the_past"
    real = client.post(base + "status/", data={"status": "open"}, content_type="application/json")
    assert real.status_code == 400 and "ends_at" in real.json()


def test_closing_counts_pending_applications_and_archiving_says_what_becomes_read_only():
    workspace, organizer, client, _, base, event = setup()
    applicant = User.objects.create_user(username="app", password="unused")
    EventApplication.objects.create(event=event, user=applicant)
    Event.objects.filter(pk=event.pk).update(status=EventStatus.OPEN)
    shown = preview(client, base, "event.close")
    pending = next(c for c in shown["consequences"] if c["code"] == "pending_applications")
    assert pending["count"] == 1
    Event.objects.filter(pk=event.pk).update(status=EventStatus.CLOSED)
    shown = preview(client, base, "event.archive")
    locked = next(c for c in shown["consequences"] if c["code"] == "read_only")["count"]
    assert (
        client.post(
            base + "status/", data={"status": "archived"}, content_type="application/json"
        ).status_code
        == 200
    )
    entries = client.get(base + "configuration/").json()["settings"]
    assert (
        locked
        == sum(1 for e in entries if e["write"] and e["lock"])
        == sum(1 for s in SPECS if s.write)
    )


def test_deleting_a_draft_event_is_stated_and_a_preset_event_is_refused_cleanly():
    workspace, organizer, client, _, base, event = setup()
    shown = preview(client, base, "event.delete")
    assert shown["allowed"] is False and shown["refusal"]["code"] == "published_rubric"
    response = client.delete(base)
    assert response.status_code == 400 and Event.objects.filter(pk=event.pk).exists()

    plain = Event.objects.create(workspace=workspace, name="By hand", slug="by-hand")
    Stage.objects.create(event=plain, name="Only", is_initial=True)
    Track.objects.create(event=plain, name="T")
    plain_base = base.replace(str(event.public_id), str(plain.public_id))
    shown = preview(client, plain_base, "event.delete")
    assert shown["allowed"] is True
    assert any("stage" in c["message"] for c in shown["consequences"] if c["code"] == "removed")
    assert client.delete(plain_base).status_code == 204
    audit = AuditEvent.objects.get(action="event.deleted")
    assert any(c["code"] == "removed" for c in audit.metadata["consequences"])

    started = Event.objects.create(
        workspace=workspace, name="Live", slug="live", status=EventStatus.OPEN
    )
    shown = preview(
        client, base.replace(str(event.public_id), str(started.public_id)), "event.delete"
    )
    assert shown["refusal"]["code"] == "not_draft"


def test_bad_requests_and_boundaries():
    workspace, _, client, judge, base, event = setup()
    assert client.get(base + "consequences/").status_code == 400
    assert client.get(base + "consequences/?action=nuke").status_code == 400
    assert client.get(base + "consequences/?action=stage.delete").status_code == 400
    assert (
        client.get(base + "consequences/?action=stage.delete&target=not-a-uuid").status_code == 400
    )
    # A stage of another event cannot be previewed through this one.
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    foreign = Stage.objects.create(event=other, name="Foreign", is_initial=True)
    assert (
        client.get(
            base + f"consequences/?action=stage.delete&target={foreign.public_id}"
        ).status_code
        == 400
    )
    assert set(ACTIONS) == {
        "event.open",
        "event.close",
        "event.archive",
        "event.delete",
        "stage.delete",
        "stage_transition.delete",
        "track.delete",
        "base_prize.delete",
    }


def test_consequences_are_organizer_only_and_tenant_scoped():
    workspace, _, client, judge, base, event = setup()
    url = base + "consequences/?action=event.open"
    assert judge.get(url).status_code == 403
    assert Client().get(url).status_code in (401, 403)
    other = Workspace.objects.create(name="Other", slug="other")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert outsider.get(url).status_code == 403
    cross = f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/consequences/"
    assert outsider.get(cross + "?action=event.open").status_code == 404
