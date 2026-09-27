import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event, EventStatus, ParticipantCheckIn
from participation.models import Team
from projects.models import MentorNote, Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def new_user(username):
    return User.objects.create_user(username=username)


def fixture():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = new_user("organizer")
    participant = new_user("participant")
    mentor = new_user("mentor")
    volunteer = new_user("volunteer")
    sponsor = new_user("sponsor")
    for user, role in [
        (organizer, Role.ORGANIZER),
        (participant, Role.PARTICIPANT),
        (mentor, Role.MENTOR),
        (volunteer, Role.VOLUNTEER),
        (sponsor, Role.SPONSOR),
    ]:
        Membership.objects.create(workspace=workspace, user=user, role=role)
    event = Event.objects.create(
        workspace=workspace,
        name="Hack",
        slug="hack",
        status=EventStatus.OPEN,
        starts_at="2027-01-01T00:00:00Z",
        ends_at="2027-01-02T00:00:00Z",
    )
    team = Team.objects.create(event=event, name="Builders")
    project = Project.objects.create(event=event, team=team, created_by=organizer, name="Robot")
    return workspace, organizer, participant, mentor, volunteer, sponsor, event, project


def project_url(workspace, event, project, suffix):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/projects/{project.public_id}/{suffix}"
    )


def event_url(workspace, event, suffix):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/{suffix}"


def test_mentor_can_leave_private_notes_others_cannot_read_or_write():
    workspace, organizer, participant, mentor, volunteer, sponsor, event, project = fixture()
    notes_url = project_url(workspace, event, project, "mentor-notes/")

    assert client(participant).get(notes_url).status_code == 403
    assert (
        client(participant)
        .post(notes_url, {"body": "sneaky"}, content_type="application/json")
        .status_code
        == 403
    )

    created = client(mentor).post(
        notes_url, {"body": "Consider caching the API calls."}, content_type="application/json"
    )
    assert created.status_code == 201
    assert created.json()["mentor_username"] == "mentor"

    listed = client(organizer).get(notes_url).json()
    assert len(listed) == 1
    assert listed[0]["body"] == "Consider caching the API calls."
    assert MentorNote.objects.get(project=project).mentor == mentor


def test_volunteer_can_check_in_a_participant_but_not_arbitrary_users():
    workspace, organizer, participant, mentor, volunteer, sponsor, event, project = fixture()
    check_ins_url = event_url(workspace, event, "check-ins/")

    assert (
        client(participant)
        .post(
            check_ins_url,
            {"participant": str(participant.public_id)},
            content_type="application/json",
        )
        .status_code
        == 403
    )

    checked_in = client(volunteer).post(
        check_ins_url, {"participant": str(participant.public_id)}, content_type="application/json"
    )
    assert checked_in.status_code == 201
    assert checked_in.json()["checked_in_by"] == "volunteer"
    assert ParticipantCheckIn.objects.filter(event=event, participant=participant).exists()

    duplicate = client(volunteer).post(
        check_ins_url, {"participant": str(participant.public_id)}, content_type="application/json"
    )
    assert duplicate.status_code == 400

    not_a_participant = client(volunteer).post(
        check_ins_url, {"participant": str(mentor.public_id)}, content_type="application/json"
    )
    assert not_a_participant.status_code == 404

    listed = client(organizer).get(check_ins_url).json()
    assert len(listed) == 1


def test_sponsor_gets_read_only_project_roster():
    workspace, organizer, participant, mentor, volunteer, sponsor, event, project = fixture()
    url = event_url(workspace, event, "sponsor-projects/")
    assert client(participant).get(url).status_code == 403
    response = client(sponsor).get(url)
    assert response.status_code == 200
    assert response.json() == [
        {
            "public_id": str(project.public_id),
            "name": "Robot",
            "team_name": "Builders",
            "track_name": None,
        }
    ]


def test_new_roles_gain_no_organizer_or_judge_access():
    workspace, organizer, participant, mentor, volunteer, sponsor, event, project = fixture()
    event_detail = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    members_url = f"/api/v1/workspaces/{workspace.public_id}/members/"
    for holder in (mentor, volunteer, sponsor):
        assert (
            client(holder)
            .patch(event_detail, {"name": "Renamed"}, content_type="application/json")
            .status_code
            == 403
        )
        assert (
            client(holder)
            .post(
                members_url,
                {"username": "someone", "role": Role.ORGANIZER},
                content_type="application/json",
            )
            .status_code
            == 403
        )
