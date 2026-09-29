import pytest
from accounts.models import Session, User, UserProfile
from audit.models import AuditEvent
from django.test import Client
from evaluations.models import JudgeExpertiseProfile
from events.models import Event
from participation.models import MarketplaceProfile
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user=None):
    result = Client()
    if user:
        result.cookies["session"] = Session.issue(user).token
    return result


def world():
    owner = User.objects.create_user(username="owner", password="unused")
    peer = User.objects.create_user(username="peer", password="unused")
    outsider = User.objects.create_user(username="outsider", password="unused")
    workspace = Workspace.objects.create(name="Event", slug="event")
    for user in (owner, peer):
        Membership.objects.create(user=user, workspace=workspace, role=Role.PARTICIPANT)
    return owner, peer, outsider, workspace


def test_profile_is_self_owned_audited_and_does_not_change_authentication():
    owner, peer, _, _ = world()
    response = client(owner).patch(
        "/api/v1/accounts/profile/",
        {
            "display_name": "Alex Rivera",
            "bio": "Building useful tools",
            "links": [{"label": "GitHub", "url": "https://github.com/alex"}],
        },
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Alex Rivera"
    assert response.json()["visibility"] == "private"
    assert owner.username == "owner"
    assert not UserProfile.objects.filter(user=peer).exists()
    audit = AuditEvent.objects.get(action="account.profile_updated")
    assert audit.actor == owner
    assert "Building useful tools" not in str(audit.metadata)
    assert client().patch(
        "/api/v1/accounts/profile/", {}, content_type="application/json"
    ).status_code in (401, 403)


@pytest.mark.parametrize(
    "payload",
    [
        {"avatar_url": "javascript:alert(1)"},
        {"links": [{"label": "Code", "url": "data:text/html,unsafe"}]},
        {"visibility": "everyone"},
        {"avatar_url": "https://user:pass@example.org/image"},
        {"links": [{"label": "Code", "url": "https://example.org", "onclick": "evil"}]},
    ],
)
def test_invalid_profile_update_is_atomic(payload):
    owner, _, _, _ = world()
    response = client(owner).patch(
        "/api/v1/accounts/profile/", payload, content_type="application/json"
    )
    assert response.status_code == 400
    assert not UserProfile.objects.exists()
    assert not AuditEvent.objects.filter(action="account.profile_updated").exists()


def test_visibility_and_workspace_boundaries_apply_without_participation_disclosures():
    owner, peer, outsider, _ = world()
    profile = UserProfile.objects.create(user=owner, display_name="Alex", bio="Private bio")
    url = f"/api/v1/accounts/people/{owner.public_id}/"
    assert client(peer).get(url).status_code == 404
    assert client(owner).get(url).json()["bio"] == "Private bio"
    profile.visibility = "members"
    profile.save()
    assert client().get(url).status_code == 404
    assert client(outsider).get(url).status_code == 404
    body = client(peer).get(url).json()
    assert body["display_name"] == "Alex"
    assert "event_profiles" not in body and "judge_expertise" not in body
    profile.visibility = "public"
    profile.save()
    assert client().get(url).json()["bio"] == "Private bio"


def test_own_profile_reuses_existing_matching_and_expertise_only_in_current_workspaces():
    owner, _, _, workspace = world()
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    MarketplaceProfile.objects.create(
        user=owner,
        event=event,
        skills=["Python"],
        roles=["builder"],
        interests=["climate"],
        visible=True,
    )
    JudgeExpertiseProfile.objects.create(judge=owner, workspace=workspace, tags=["security"])
    other = Workspace.objects.create(name="Old", slug="old")
    JudgeExpertiseProfile.objects.create(judge=owner, workspace=other, tags=["private-other"])
    body = client(owner).get("/api/v1/accounts/profile/").json()
    assert body["event_profiles"][0]["skills"] == ["Python"]
    assert body["event_profiles"][0]["team_seeking"] is True
    assert body["judge_expertise"] == [
        {"workspace": str(workspace.public_id), "tags": ["security"]}
    ]
    assert not UserProfile.objects.exists()


def test_reusable_tags_follow_identity_privacy_without_changing_event_matching():
    owner, peer, _, workspace = world()
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    market = MarketplaceProfile.objects.create(
        user=owner, event=event, skills=["Rust"], visible=False
    )
    response = client(owner).patch(
        "/api/v1/accounts/profile/",
        {"skills": ["Python"], "interests": ["Climate"], "preferred_roles": ["Builder"]},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["skills"] == ["Python"]
    market.refresh_from_db()
    assert market.skills == ["Rust"] and market.visible is False
    url = f"/api/v1/accounts/people/{owner.public_id}/"
    assert client(peer).get(url).status_code == 404
    profile = UserProfile.objects.get(user=owner)
    profile.visibility = "members"
    profile.save()
    assert client(peer).get(url).json()["skills"] == ["Python"]
    before = profile.skills
    response = client(owner).patch(
        "/api/v1/accounts/profile/",
        {"skills": ["Python", "python"]},
        content_type="application/json",
    )
    assert response.status_code == 400
    profile.refresh_from_db()
    assert profile.skills == before
