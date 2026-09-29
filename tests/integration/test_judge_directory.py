import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from evaluations.models import EvaluationPool, JudgeInvitation, PoolMembership
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def url(workspace, suffix):
    return f"/api/v1/workspaces/{workspace.public_id}/{suffix}"


def fixture():
    organizer = User.objects.create_user(username="organizer")
    judge = User.objects.create_user(username="judge")
    other = User.objects.create_user(username="other")
    workspace = Workspace.objects.create(name="One", slug="one")
    other_workspace = Workspace.objects.create(name="Two", slug="two")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=other, workspace=other_workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="First", slug="first")
    second_event = Event.objects.create(workspace=workspace, name="Second", slug="second")
    pool = EvaluationPool.objects.create(event=event, name="Panel")
    second_pool = EvaluationPool.objects.create(event=second_event, name="Panel")
    return organizer, judge, other, workspace, other_workspace, event, pool, second_pool


def test_directory_and_invitation_acceptance_are_workspace_and_event_scoped():
    organizer, judge, other, workspace, _, event, pool, second_pool = fixture()
    organizer_client = client(organizer)
    judge_client = client(judge)
    directory = url(workspace, "judge-directory/")
    invite = url(workspace, f"events/{event.public_id}/judge-invitations/")

    assert organizer_client.get(directory).json() == [
        {
            "judge": str(judge.public_id),
            "username": "judge",
            "identity": {
                "user_public_id": str(judge.public_id),
                "username": "judge",
                "display_name": "judge",
                "avatar_url": "",
                "bio": "",
                "location": "",
                "links": [],
                "profile_url": "",
                "skills": [],
                "interests": [],
                "preferred_roles": [],
            },
        }
    ]
    assert judge_client.get(directory).status_code == 403
    assert (
        organizer_client.post(
            invite,
            {"pool": str(pool.public_id), "judge": str(other.public_id)},
            content_type="application/json",
        ).status_code
        == 400
    )
    assert (
        organizer_client.post(
            invite,
            {"pool": str(second_pool.public_id), "judge": str(judge.public_id)},
            content_type="application/json",
        ).status_code
        == 404
    )

    response = organizer_client.post(
        invite,
        {"pool": str(pool.public_id), "judge": str(judge.public_id)},
        content_type="application/json",
    )
    assert response.status_code == 201
    invitation_id = response.json()["public_id"]
    assert not PoolMembership.objects.filter(pool=pool, judge=judge).exists()
    my_invitations = judge_client.get(url(workspace, "my-judge-invitations/")).json()
    assert my_invitations[0]["status"] == "pending"
    assert client(other).get(url(workspace, "my-judge-invitations/")).status_code == 403

    respond = url(workspace, f"my-judge-invitations/{invitation_id}/respond/")
    assert (
        judge_client.post(respond, {"decision": "accept"}, content_type="application/json").json()[
            "status"
        ]
        == "accepted"
    )
    assert PoolMembership.objects.filter(pool=pool, judge=judge).count() == 1
    assert not PoolMembership.objects.filter(pool=second_pool, judge=judge).exists()
    assert (
        judge_client.post(
            respond, {"decision": "accept"}, content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        organizer_client.post(
            invite,
            {"pool": str(pool.public_id), "judge": str(judge.public_id)},
            content_type="application/json",
        ).status_code
        == 400
    )
    accepted_events = AuditEvent.objects.filter(
        workspace=workspace, action="judge_invitation.accepted"
    )
    assert accepted_events.count() == 1


def test_decline_reinvite_and_revocation_do_not_grant_access():
    organizer, judge, _, workspace, _, event, pool, _ = fixture()
    organizer_client, judge_client = client(organizer), client(judge)
    invite = url(workspace, f"events/{event.public_id}/judge-invitations/")
    data = {"pool": str(pool.public_id), "judge": str(judge.public_id)}
    invitation_id = organizer_client.post(invite, data, content_type="application/json").json()[
        "public_id"
    ]
    respond = url(workspace, f"my-judge-invitations/{invitation_id}/respond/")
    assert organizer_client.post(invite, data, content_type="application/json").status_code == 400
    assert (
        judge_client.post(respond, {"decision": "decline"}, content_type="application/json").json()[
            "status"
        ]
        == "declined"
    )
    assert not PoolMembership.objects.filter(pool=pool, judge=judge).exists()

    assert organizer_client.post(invite, data, content_type="application/json").status_code == 201
    revoke = url(workspace, f"events/{event.public_id}/judge-invitations/{invitation_id}/")
    assert organizer_client.delete(revoke).status_code == 204
    assert (
        judge_client.post(
            respond, {"decision": "accept"}, content_type="application/json"
        ).status_code
        == 400
    )
    assert not PoolMembership.objects.filter(pool=pool, judge=judge).exists()
    assert JudgeInvitation.objects.get(public_id=invitation_id).status == "revoked"


def test_removed_judge_role_fails_closed_and_other_judge_cannot_respond():
    organizer, judge, _, workspace, _, event, pool, _ = fixture()
    peer = User.objects.create_user(username="peer")
    Membership.objects.create(user=peer, workspace=workspace, role=Role.JUDGE)
    invitation_id = (
        client(organizer)
        .post(
            url(workspace, f"events/{event.public_id}/judge-invitations/"),
            {"pool": str(pool.public_id), "judge": str(judge.public_id)},
            content_type="application/json",
        )
        .json()["public_id"]
    )
    respond = url(workspace, f"my-judge-invitations/{invitation_id}/respond/")
    assert (
        client(peer)
        .post(respond, {"decision": "accept"}, content_type="application/json")
        .status_code
        == 404
    )
    Membership.objects.filter(user=judge, workspace=workspace, role=Role.JUDGE).delete()
    assert (
        client(judge)
        .post(respond, {"decision": "accept"}, content_type="application/json")
        .status_code
        == 403
    )
    assert not PoolMembership.objects.filter(pool=pool, judge=judge).exists()


def test_pool_bound_plan_rejects_ballots_until_invitation_is_accepted():
    organizer, judge, _, workspace, _, event, pool, _ = fixture()
    stage = Stage.objects.create(event=event, name="Final")
    project = Project.objects.create(event=event, name="Entry", created_by=organizer)
    Submission.objects.create(project=project, stage=stage, updated_by=organizer)
    organizer_client, judge_client = client(organizer), client(judge)
    plans = url(
        workspace,
        f"events/{event.public_id}/stages/{stage.public_id}/evaluation-plans/",
    )
    plan_response = organizer_client.post(
        plans,
        {
            "name": "Panel",
            "pool": str(pool.public_id),
            "draft_criteria": [
                {"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}
            ],
        },
        content_type="application/json",
    )
    assert plan_response.status_code == 201, plan_response.content
    plan = plans + plan_response.json()["public_id"] + "/"
    assert organizer_client.post(plan + "publish-rubric/").status_code == 201
    ballot = {
        "project": str(project.public_id),
        "responses": [{"criterion_id": "impact", "score": 8}],
    }
    assert judge_client.get(plan + "candidates/").json() == []
    assert (
        judge_client.post(plan + "ballots/", ballot, content_type="application/json").status_code
        == 400
    )

    invitation = organizer_client.post(
        url(workspace, f"events/{event.public_id}/judge-invitations/"),
        {"pool": str(pool.public_id), "judge": str(judge.public_id)},
        content_type="application/json",
    )
    assert invitation.status_code == 201
    assert judge_client.get(plan + "candidates/").json() == []
    invitation_id = invitation.json()["public_id"]
    assert (
        judge_client.post(
            url(workspace, f"my-judge-invitations/{invitation_id}/respond/"),
            {"decision": "accept"},
            content_type="application/json",
        ).status_code
        == 200
    )
    assert [row["project"] for row in judge_client.get(plan + "candidates/").json()] == [
        str(project.public_id)
    ]
    assert (
        judge_client.post(plan + "ballots/", ballot, content_type="application/json").status_code
        == 201
    )
