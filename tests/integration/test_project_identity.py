import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from django.test import Client
from events.models import Event, Track
from participation.models import Team, TeamMembership, TeamMembershipRole
from projects.models import Project, ProjectMembership, ProjectMembershipRole
from projects.services import create_project, update_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_event():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    creator = User.objects.create_user(username="creator", password="unused")
    Membership.objects.create(workspace=workspace, user=creator, role=Role.PARTICIPANT)
    return workspace, event, creator


def test_project_has_durable_identity_and_creator_membership():
    _, event, creator = setup_event()
    project = create_project(event, creator, "Prototype")
    assert Project.objects.get(public_id=project.public_id).name == "Prototype"
    assert project.memberships.get(user=creator).role == ProjectMembershipRole.OWNER
    assert project.event == event


def test_project_rejects_team_from_another_event():
    workspace, event, creator = setup_event()
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    team = Team.objects.create(event=other, name="Other team")
    TeamMembership.objects.create(team=team, user=creator, role=TeamMembershipRole.CAPTAIN)
    with pytest.raises(ValidationError, match="Team must belong"):
        create_project(event, creator, "Wrong event", team=team)
    assert not Project.objects.exists()


def test_project_rejects_creator_outside_workspace_or_team():
    _, event, creator = setup_event()
    outsider = User.objects.create_user(username="outsider", password="unused")
    with pytest.raises(ValidationError, match="workspace"):
        create_project(event, outsider, "No membership")
    team = Team.objects.create(event=event, name="A")
    with pytest.raises(ValidationError, match="project team"):
        create_project(event, creator, "No team membership", team=team)


def test_project_can_be_created_with_a_track_from_the_same_event():
    _, event, creator = setup_event()
    track = Track.objects.create(event=event, name="AI")
    project = create_project(event, creator, "Prototype", track=track)
    assert project.track == track


def test_project_rejects_track_from_another_event():
    workspace, event, creator = setup_event()
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    other_track = Track.objects.create(event=other, name="Other track")
    with pytest.raises(ValidationError, match="Track must belong"):
        create_project(event, creator, "Wrong event track", track=other_track)
    assert not Project.objects.exists()


def test_project_without_a_track_is_still_valid():
    _, event, creator = setup_event()
    project = create_project(event, creator, "No track yet")
    assert project.track is None


def test_update_project_can_set_and_clear_the_track():
    _, event, creator = setup_event()
    track = Track.objects.create(event=event, name="AI")
    project = create_project(event, creator, "Prototype")
    updated = update_project(project, creator, track=track, track_set=True)
    assert updated.track == track
    cleared = update_project(project, creator, track=None, track_set=True)
    assert cleared.track is None


def test_project_membership_is_unique_and_scoped_to_workspace():
    _, event, creator = setup_event()
    project = create_project(event, creator, "A")
    outsider = User.objects.create_user(username="outsider", password="unused")
    with pytest.raises(ValidationError, match="event workspace"):
        ProjectMembership(
            project=project, user=outsider, role=ProjectMembershipRole.CONTRIBUTOR
        ).full_clean()
    with pytest.raises(ValidationError):
        ProjectMembership(
            project=project, user=creator, role=ProjectMembershipRole.CONTRIBUTOR
        ).full_clean()


def client_for(user):
    from accounts.models import Session

    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def test_project_api_scopes_listing_and_member_addition():
    workspace, event, owner = setup_event()
    contributor = User.objects.create_user(username="contributor", password="unused")
    Membership.objects.create(workspace=workspace, user=contributor, role=Role.PARTICIPANT)
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/projects/"
    created = client_for(owner).post(base, {"name": "Prototype"}, content_type="application/json")
    assert created.status_code == 201
    project_id = created.json()["public_id"]
    assert client_for(contributor).get(base).json() == []
    assert client_for(contributor).get(base + project_id + "/").status_code == 404
    assert (
        client_for(contributor)
        .post(
            base + project_id + "/members/",
            {"user": str(owner.public_id)},
            content_type="application/json",
        )
        .status_code
        == 404
    )
    added = client_for(owner).post(
        base + project_id + "/members/",
        {"user": str(contributor.public_id)},
        content_type="application/json",
    )
    assert added.status_code == 201
    assert added.json()["role"] == "contributor"
    assert len(client_for(contributor).get(base).json()) == 1


def test_project_api_creates_with_track_and_supports_patching_it():
    workspace, event, owner = setup_event()
    track = Track.objects.create(event=event, name="AI")
    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    other_track = Track.objects.create(event=other_event, name="Cross-event")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/projects/"

    created = client_for(owner).post(
        base,
        {"name": "Prototype", "track": str(track.public_id)},
        content_type="application/json",
    )
    assert created.status_code == 201
    assert created.json()["track"] == str(track.public_id)
    project_url = base + created.json()["public_id"] + "/"

    cross_event = client_for(owner).patch(
        project_url, {"track": str(other_track.public_id)}, content_type="application/json"
    )
    assert cross_event.status_code == 404  # other_track isn't found scoped to this event

    cleared = client_for(owner).patch(project_url, {"track": None}, content_type="application/json")
    assert cleared.status_code == 200
    assert cleared.json()["track"] is None


def test_project_api_rejects_nonmember_and_missing_name():
    workspace, event, _ = setup_event()
    outsider = User.objects.create_user(username="outsider", password="unused")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/projects/"
    assert client_for(outsider).post(
        base, {"name": "No"}, content_type="application/json"
    ).status_code in (401, 403)
    owner = User.objects.get(username="creator")
    assert client_for(owner).post(base, {}, content_type="application/json").status_code == 400
