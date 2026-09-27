import pytest
from accounts.models import Session, User
from core.permission_matrix import build_permission_matrix, dry_run
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def find(matrix, view_name, method):
    return next(e for e in matrix if e["view"] == view_name and e["method"] == method)


def test_hypothetical_role_dry_run_matches_the_static_matrix():
    workspace = Workspace.objects.create(name="One", slug="one")
    entry = find(build_permission_matrix(), "TrackListView", "POST")

    denied = dry_run(
        path=entry["path"],
        method="POST",
        workspace=workspace,
        subject_kind="role",
        subject="participant",
    )
    assert denied == {
        "allowed": False,
        "mode": "hypothetical",
        "access": "roles",
        "roles": entry["roles"],
    }

    allowed = dry_run(
        path=entry["path"],
        method="POST",
        workspace=workspace,
        subject_kind="role",
        subject="organizer",
    )
    assert allowed["allowed"] is True
    assert allowed["mode"] == "hypothetical"


def test_live_dry_run_reflects_a_real_users_actual_roles():
    workspace = Workspace.objects.create(name="One", slug="one")
    judge = User.objects.create_user(username="judge")
    participant = User.objects.create_user(username="participant")
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    Membership.objects.create(workspace=workspace, user=participant, role=Role.PARTICIPANT)
    entry = find(build_permission_matrix(), "CalibrationBallotListCreateView", "GET")

    as_judge = dry_run(
        path=entry["path"], method="GET", workspace=workspace, subject_kind="user", subject=judge
    )
    assert as_judge["allowed"] is True
    assert as_judge["mode"] == "live"
    assert as_judge["actual_roles"] == ["judge"]

    as_participant = dry_run(
        path=entry["path"],
        method="GET",
        workspace=workspace,
        subject_kind="user",
        subject=participant,
    )
    assert as_participant["allowed"] is False
    assert as_participant["actual_roles"] == ["participant"]


def test_dry_run_endpoint_is_organizer_only_and_validates_input():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    participant = User.objects.create_user(username="participant")
    judge = User.objects.create_user(username="judge")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=participant, role=Role.PARTICIPANT)
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/authz-dry-run/"
    entry = find(build_permission_matrix(), "TrackListView", "POST")

    assert (
        client(participant)
        .post(
            url,
            {"path": entry["path"], "method": "POST", "subject_kind": "role", "subject": "judge"},
            content_type="application/json",
        )
        .status_code
        == 403
    )

    bad_role = client(organizer).post(
        url,
        {"path": entry["path"], "method": "POST", "subject_kind": "role", "subject": "nope"},
        content_type="application/json",
    )
    assert bad_role.status_code == 400

    bad_path = client(organizer).post(
        url,
        {
            "path": "not/a/real/path/",
            "method": "GET",
            "subject_kind": "role",
            "subject": "organizer",
        },
        content_type="application/json",
    )
    assert bad_path.status_code == 400

    live = client(organizer).post(
        url,
        {
            "path": entry["path"],
            "method": "POST",
            "subject_kind": "user",
            "subject": str(judge.public_id),
        },
        content_type="application/json",
    )
    assert live.status_code == 200
    assert live.json() == {"allowed": False, "mode": "live", "actual_roles": ["judge"]}
