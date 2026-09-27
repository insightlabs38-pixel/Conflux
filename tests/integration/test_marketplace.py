import pytest
from accounts.models import Session, User
from django.test import Client
from django.utils import timezone
from events.models import Event
from participation.models import Team, TeamMembership, TeamMembershipRole
from projects.models import Project
from stages.models import ParticipationMode, Stage, StageEntry
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_case():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    captain = User.objects.create_user(username="captain", password="unused")
    seeker = User.objects.create_user(username="seeker", password="unused")
    outsider = User.objects.create_user(username="outsider", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    for user, role in [
        (captain, Role.PARTICIPANT),
        (seeker, Role.PARTICIPANT),
        (judge, Role.JUDGE),
    ]:
        Membership.objects.create(workspace=workspace, user=user, role=role)
    team = Team.objects.create(event=event, name="Builders")
    TeamMembership.objects.create(team=team, user=captain, role=TeamMembershipRole.CAPTAIN)
    project = Project.objects.create(event=event, team=team, created_by=captain, name="Robot")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/marketplace/"
    return workspace, event, captain, seeker, outsider, judge, team, project, base


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def save_profile(client, base, *, skills, visible):
    return client.put(
        base + "profile/",
        {"skills": skills, "bio": "Available", "visible": visible},
        content_type="application/json",
    )


def create_opening(client, base, *, project=None, title="Builder", skills=None):
    return client.post(
        base + "openings/",
        {
            "title": title,
            "desired_skills": skills or ["python"],
            "project": str(project.public_id) if project else None,
        },
        content_type="application/json",
    )


def test_opt_in_profile_visibility_and_participant_access():
    _, _, captain, seeker, outsider, judge, _, _, base = setup_case()
    captain_client = client_for(captain)
    seeker_client = client_for(seeker)
    assert seeker_client.get(base + "profile/").json() == {"profile": None}
    assert (
        save_profile(seeker_client, base, skills=["Python", "python"], visible=False).status_code
        == 200
    )
    assert seeker_client.get(base + "profile/").json()["profile"]["skills"] == ["python"]
    assert captain_client.get(base + "profiles/").json() == []
    assert save_profile(seeker_client, base, skills=["Python"], visible=True).status_code == 200
    assert captain_client.get(base + "profiles/").json()[0]["username"] == "seeker"
    assert client_for(judge).get(base + "profiles/").status_code == 403
    assert client_for(outsider).get(base + "profiles/").status_code in (401, 403)


def test_captain_controls_openings_and_project_identity():
    workspace, event, captain, seeker, _, _, team, project, base = setup_case()
    captain_client = client_for(captain)
    assert create_opening(client_for(seeker), base, project=project).status_code == 400
    alien_team = Team.objects.create(event=event, name="Alien")
    alien_project = Project.objects.create(
        event=event, team=alien_team, created_by=seeker, name="Alien project"
    )
    assert create_opening(captain_client, base, project=alien_project).status_code == 404
    created = create_opening(captain_client, base, project=project)
    assert created.status_code == 201
    opening_id = created.json()["public_id"]
    assert created.json()["project_name"] == "Robot"
    assert len(client_for(seeker).get(base + "openings/").json()) == 1
    assert client_for(seeker).get(base + "matches/").json()[0]["title"] == "Builder"
    closed = captain_client.patch(
        base + f"openings/{opening_id}/", {"is_open": False}, content_type="application/json"
    )
    assert closed.status_code == 200
    assert client_for(seeker).get(base + "openings/").json() == []
    assert captain_client.get(base + "my-openings/").json()[0]["is_open"] is False
    assert (
        client_for(seeker)
        .patch(base + f"openings/{opening_id}/", {"is_open": True}, content_type="application/json")
        .status_code
        == 400
    )


def test_matching_ranks_overlap_and_hides_teamed_profiles():
    _, event, captain, seeker, _, _, team, project, base = setup_case()
    captain_client = client_for(captain)
    seeker_client = client_for(seeker)
    save_profile(seeker_client, base, skills=["Python", "Design"], visible=True)
    first = create_opening(captain_client, base, project=project, title="Python", skills=["python"])
    create_opening(captain_client, base, title="Rust", skills=["rust"])
    matches = seeker_client.get(base + "matches/").json()
    assert [item["title"] for item in matches] == ["Python", "Rust"]
    assert matches[0]["matched_skills"] == ["python"]
    opening_id = first.json()["public_id"]
    assert (
        captain_client.get(base + f"openings/{opening_id}/matches/").json()[0]["username"]
        == "seeker"
    )
    assert seeker_client.get(base + f"openings/{opening_id}/matches/").status_code == 400
    TeamMembership.objects.create(team=team, user=seeker)
    assert captain_client.get(base + f"openings/{opening_id}/matches/").json() == []
    assert seeker_client.get(base + "matches/").json() == []


def test_full_and_team_locked_openings_disappear_from_discovery():
    workspace, event, captain, seeker, _, _, team, _, base = setup_case()
    captain_client = client_for(captain)
    assert create_opening(captain_client, base).status_code == 201
    assert len(client_for(seeker).get(base + "openings/").json()) == 1
    stage = Stage.objects.create(
        event=event, name="Locked", participation_mode=ParticipationMode.TEAM_LOCKED
    )
    entry = StageEntry.objects.enter(stage, "team", str(team.public_id))
    assert client_for(seeker).get(base + "openings/").json() == []
    entry.exited_at = timezone.now()
    entry.save(update_fields=["exited_at"])
    for index in range(2):
        user = User.objects.create_user(username=f"extra-{index}", password="unused")
        Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
        TeamMembership.objects.create(team=team, user=user)
    assert len(client_for(seeker).get(base + "openings/").json()) == 1
    TeamMembership.objects.create(team=team, user=seeker)
    assert client_for(captain).get(base + "openings/").json() == []
