from datetime import timedelta

import pytest
from accounts.models import Session, User
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from events.models import Event, Track
from integrations.archive import build_archive, import_archive
from mentorship.models import MentorProfile, MentorRequest, OfficeHourSignup, OfficeHourSlot
from mentorship.services import (
    MAX_ACTIVE_REQUESTS_PER_PROJECT,
    cancel_office_hours_signup,
    cancel_request,
    claim_request,
    create_request,
    reassign_request,
    resolve_request,
    sign_up_for_office_hours,
)
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"


def world():
    workspace = Workspace.objects.create(name="M", slug="m")
    event = Event.objects.create(workspace=workspace, name="E", slug="e", status="open")
    organizer = User.objects.create_user(username="organizer")
    mentor = User.objects.create_user(username="mentor")
    other_mentor = User.objects.create_user(username="other-mentor")
    participant = User.objects.create_user(username="participant")
    other_participant = User.objects.create_user(username="other-participant")
    outsider = User.objects.create_user(username="outsider")
    for user, role in [
        (organizer, Role.ORGANIZER),
        (mentor, Role.MENTOR),
        (other_mentor, Role.MENTOR),
        (participant, Role.PARTICIPANT),
        (other_participant, Role.PARTICIPANT),
    ]:
        Membership.objects.create(workspace=workspace, user=user, role=role)
    project = create_project(event, participant, "Project")
    return (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    )


def test_only_mentor_like_users_can_hold_or_see_a_profile():
    (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    ) = world()
    url = base(workspace, event) + "mentors/me/"
    denied = client_for(participant).put(url, {"headline": "Nope"}, content_type="application/json")
    assert denied.status_code == 400

    track = Track.objects.create(event=event, name="FinTech")
    saved = client_for(mentor).put(
        url,
        {"headline": "Backend help", "track_expertise": [str(track.public_id)]},
        content_type="application/json",
    )
    assert saved.status_code == 200
    assert saved.json()["track_expertise"] == [str(track.public_id)]

    listed = client_for(participant).get(base(workspace, event) + "mentors/").json()
    assert [row["mentor"] for row in listed] == ["mentor"]


def test_request_queue_is_bounded_per_project():
    (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    ) = world()
    other_project = create_project(event, other_participant, "Other")
    with pytest.raises(ValidationError, match="request"):
        create_request(other_project, participant, topic="x", urgency="normal")

    for i in range(MAX_ACTIVE_REQUESTS_PER_PROJECT):
        create_request(project, participant, topic=f"Help {i}", urgency="normal")
    with pytest.raises(ValidationError, match="open requests"):
        create_request(project, participant, topic="One more", urgency="normal")


def test_claim_reassign_resolve_and_cancel_lifecycle_and_authorization():
    (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    ) = world()
    request = create_request(project, participant, topic="Stuck on auth", urgency="urgent")

    with pytest.raises(ValidationError, match="mentor or organizer"):
        claim_request(request, outsider)
    claimed = claim_request(request, mentor)
    assert claimed.status == "claimed" and claimed.claimed_by == mentor
    with pytest.raises(ValidationError, match="pending"):
        claim_request(claimed, other_mentor)

    with pytest.raises(ValidationError, match="organizer"):
        reassign_request(claimed, mentor, to_mentor=other_mentor)
    reassigned = reassign_request(claimed, organizer, to_mentor=other_mentor)
    assert reassigned.claimed_by == other_mentor

    with pytest.raises(ValidationError, match="claiming mentor or an organizer"):
        resolve_request(reassigned, mentor, note="not mine")
    resolved = resolve_request(reassigned, other_mentor, note="Paired and fixed it.")
    assert resolved.status == "resolved" and resolved.resolution_note == "Paired and fixed it."

    second = create_request(project, participant, topic="Another thing", urgency="low")
    with pytest.raises(ValidationError, match="requester or an organizer"):
        cancel_request(second, outsider)
    cancelled = cancel_request(second, participant)
    assert cancelled.status == "cancelled"


def test_participant_sees_own_request_status_and_resolution_but_not_the_queue():
    (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    ) = world()
    request = create_request(project, participant, topic="Need a hand", urgency="normal")
    claim_request(request, mentor)
    resolve_request(MentorRequest.objects.get(pk=request.pk), mentor, note="All set.")

    own = client_for(participant).get(
        base(workspace, event) + f"projects/{project.public_id}/mentor-requests/"
    )
    assert own.status_code == 200
    row = own.json()[0]
    assert row["status"] == "resolved" and row["resolution_note"] == "All set."

    assert (
        client_for(participant).get(base(workspace, event) + "mentor-requests/queue/").status_code
        == 400
    )
    assert (
        client_for(mentor).get(base(workspace, event) + "mentor-requests/queue/").status_code == 200
    )
    non_member = client_for(other_participant).get(
        base(workspace, event) + f"projects/{project.public_id}/mentor-requests/"
    )
    assert non_member.status_code == 404
    assert (
        client_for(outsider).get(base(workspace, event) + "mentor-requests/queue/").status_code
        == 403
    )


def test_office_hours_capacity_attendee_visibility_and_signup_cancellation():
    (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    ) = world()
    second_project = create_project(event, other_participant, "Second")
    starts = timezone.now() + timedelta(hours=1)
    slot = OfficeHourSlot.objects.create(
        event=event, mentor=mentor, starts_at=starts, ends_at=starts + timedelta(minutes=30)
    )

    signup = sign_up_for_office_hours(slot, project, participant)
    assert OfficeHourSignup.objects.filter(pk=signup.pk).exists()
    with pytest.raises(ValidationError, match="already signed up"):
        sign_up_for_office_hours(slot, project, participant)
    with pytest.raises(ValidationError, match="full"):
        sign_up_for_office_hours(slot, second_project, other_participant)

    mine = client_for(participant).get(base(workspace, event) + "office-hours/").json()[0]
    assert mine["my_signup"] == str(signup.public_id) and "attendees" not in mine
    managed = client_for(mentor).get(base(workspace, event) + "office-hours/").json()[0]
    assert managed["attendees"] == [{"public_id": str(signup.public_id), "project": "Project"}]

    with pytest.raises(ValidationError, match="project member or an organizer"):
        cancel_office_hours_signup(signup, outsider)
    cancel_office_hours_signup(signup, participant)
    assert not OfficeHourSignup.objects.filter(pk=signup.pk).exists()


def test_mentorship_rows_survive_a_final_archive_round_trip():
    (
        workspace,
        event,
        organizer,
        mentor,
        other_mentor,
        participant,
        other_participant,
        outsider,
        project,
    ) = world()
    track = Track.objects.create(event=event, name="FinTech")
    profile = MentorProfile.objects.create(event=event, mentor=mentor, headline="Backend")
    profile.track_expertise.set([track])
    request = create_request(project, participant, track=track, topic="Need help", urgency="low")
    claim_request(request, mentor)
    starts = timezone.now() + timedelta(hours=1)
    slot = OfficeHourSlot.objects.create(
        event=event,
        mentor=mentor,
        track=track,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
    )
    sign_up_for_office_hours(slot, project, participant)

    archive = build_archive(event, mode="final")
    copied = import_archive(workspace=workspace, archive=archive, name="Copy", slug="copy")

    copied_profile = MentorProfile.objects.get(event=copied, mentor__username="mentor")
    assert [t.name for t in copied_profile.track_expertise.all()] == ["FinTech"]
    copied_request = MentorRequest.objects.get(event=copied)
    assert copied_request.status == "claimed" and copied_request.claimed_by.username == "mentor"
    copied_slot = OfficeHourSlot.objects.get(event=copied)
    assert copied_slot.signups.get().project.name == "Project"
