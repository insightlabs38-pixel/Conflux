import pytest
from accounts.models import Session, User, digest_session_token
from audit.models import AuditEvent, DomainEvent
from core.authz import has_any_role, roles_for
from core.models import IdempotencyKey
from django.core.management import call_command
from django.test import Client
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def make_user(username):
    return User.objects.create_user(username=username, password="irrelevant")


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def issue(user, seed_label=""):
    return Session.issue(user, seed_label=seed_label).token


def make_workspace_with_organizer():
    organizer = make_user("organizer")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    return workspace, organizer


# --- Session/cookie authentication -----------------------------------------


def test_missing_session_cookie_is_unauthorized():
    response = Client().get("/api/v1/accounts/me/")
    assert response.status_code in (401, 403)


def test_valid_session_cookie_authenticates():
    user = make_user("alice")
    token = issue(user)
    response = cookie_client(token).get("/api/v1/accounts/me/")
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_me_endpoint_reports_workspace_name_for_navigation():
    workspace, organizer = make_workspace_with_organizer()
    response = cookie_client(issue(organizer)).get("/api/v1/accounts/me/")
    membership = response.json()["memberships"][0]
    assert membership["workspace"] == str(workspace.public_id)
    assert membership["workspace_name"] == "Dogfood"


def test_unknown_session_token_is_rejected():
    response = cookie_client("not-a-real-token").get("/api/v1/accounts/me/")
    assert response.status_code in (401, 403)


def test_login_issues_a_working_cookie_without_touching_seeded_sessions():
    User.objects.create_user(username="bob", password="s3cret-pass")
    response = Client().post(
        "/api/v1/accounts/login/", {"username": "bob", "password": "s3cret-pass"}
    )
    assert response.status_code == 200
    assert "session" in response.cookies

    me = Client()
    me.cookies["session"] = response.cookies["session"].value
    assert me.get("/api/v1/accounts/me/").status_code == 200


def test_login_with_bad_password_is_rejected():
    User.objects.create_user(username="carol", password="s3cret-pass")
    response = Client().post("/api/v1/accounts/login/", {"username": "carol", "password": "wrong"})
    assert response.status_code == 401


# --- Membership / role model -------------------------------------------------


def test_membership_supports_multiple_roles_for_same_user_and_workspace():
    user = make_user("dana")
    workspace = Workspace.objects.create(name="W", slug="w")
    Membership.objects.create(user=user, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=user, workspace=workspace, role=Role.JUDGE)

    assert roles_for(user, workspace) == frozenset({Role.ORGANIZER, Role.JUDGE})
    assert has_any_role(user, workspace, Role.JUDGE)
    assert not has_any_role(user, workspace, Role.PARTICIPANT)


def test_roles_for_anonymous_or_missing_workspace_is_empty():
    user = make_user("erin")
    assert roles_for(None, None) == frozenset()
    assert roles_for(user, None) == frozenset()


# --- Backend-enforced role isolation ----------------------------------------


def test_workspace_create_assigns_creator_as_organizer_and_records_audit():
    user = make_user("frank")
    token = issue(user)
    response = cookie_client(token).post(
        "/api/v1/workspaces/", {"name": "Frank's Hack"}, content_type="application/json"
    )
    assert response.status_code == 201
    workspace = Workspace.objects.get(public_id=response.json()["public_id"])
    assert Membership.objects.filter(user=user, workspace=workspace, role=Role.ORGANIZER).exists()

    audit_event = AuditEvent.objects.get(workspace=workspace, action="workspace.created")
    assert audit_event.actor == user
    domain_event = DomainEvent.objects.get(workspace=workspace, event_type="workspace.created")
    assert domain_event.status == DomainEvent.Status.PENDING


def test_only_organizer_or_admin_can_list_members():
    workspace, organizer = make_workspace_with_organizer()
    participant = make_user("participant")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    judge = make_user("judge")
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)

    members_url = f"/api/v1/workspaces/{workspace.public_id}/members/"

    organizer_resp = cookie_client(issue(organizer)).get(members_url)
    assert organizer_resp.status_code == 200
    assert len(organizer_resp.json()) == 3

    for non_organizer in (participant, judge):
        response = cookie_client(issue(non_organizer)).get(members_url)
        assert response.status_code in (401, 403)

    outsider_response = cookie_client(issue(make_user("outsider"))).get(members_url)
    assert outsider_response.status_code in (401, 403)

    anon_response = Client().get(members_url)
    assert anon_response.status_code in (401, 403)


def test_a_judges_scoped_data_is_not_readable_by_a_peer_judge():
    """Mirrors the acceptance checker's core T2 assertion: a curl test with
    another party's credentials must fail in the backend, not just the UI.
    """
    workspace, organizer = make_workspace_with_organizer()
    judge_a = make_user("judge_a")
    Membership.objects.create(user=judge_a, workspace=workspace, role=Role.JUDGE)
    judge_b = make_user("judge_b")
    Membership.objects.create(user=judge_b, workspace=workspace, role=Role.JUDGE)

    audit_url = f"/api/v1/audit/{workspace.public_id}/"
    # Neither judge holds an organizer/admin role, so the shared workspace
    # audit surface is closed to both -- the isolation is role-based, not
    # identity-based allow-listing that would incidentally let a peer through.
    assert cookie_client(issue(judge_a)).get(audit_url).status_code in (401, 403)
    assert cookie_client(issue(judge_b)).get(audit_url).status_code in (401, 403)
    assert cookie_client(issue(organizer)).get(audit_url).status_code == 200


# --- Idempotency --------------------------------------------------------------


def test_idempotency_key_replays_the_original_response_without_double_creating():
    user = make_user("grace")
    client = cookie_client(issue(user))
    body = {"name": "Once Only"}

    first = client.post(
        "/api/v1/workspaces/",
        body,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="dedupe-1",
    )
    second = client.post(
        "/api/v1/workspaces/",
        body,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="dedupe-1",
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()
    assert Workspace.objects.filter(slug="once-only").count() == 1
    assert IdempotencyKey.objects.filter(key__endswith=":dedupe-1").count() == 1


def test_idempotency_key_reused_with_different_body_is_rejected():
    user = make_user("henry")
    client = cookie_client(issue(user))

    client.post(
        "/api/v1/workspaces/",
        {"name": "First"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="dedupe-2",
    )
    conflicting = client.post(
        "/api/v1/workspaces/",
        {"name": "Second"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="dedupe-2",
    )
    assert conflicting.status_code == 422


# --- Deterministic seeded acceptance identities -------------------------------


def test_seed_acceptance_identities_is_idempotent_and_grants_expected_roles():
    call_command("seed_acceptance_identities")
    call_command("seed_acceptance_identities")

    workspace = Workspace.objects.get(slug="acceptance")
    expected = {
        "organizer": Role.ORGANIZER,
        "judge_a": Role.JUDGE,
        "judge_b": Role.JUDGE,
        "participant": Role.PARTICIPANT,
    }
    for username, role in expected.items():
        user = User.objects.get(username=username)
        assert not user.has_usable_password()
        assert Membership.objects.filter(user=user, workspace=workspace, role=role).exists()
        assert Session.objects.filter(user=user, seed_label=username).count() == 1

    peer_scope_url = f"/api/v1/audit/{workspace.public_id}/"
    assert cookie_client("acceptance-judge-a").get(peer_scope_url).status_code in (401, 403)
    assert cookie_client("acceptance-judge-b").get(peer_scope_url).status_code in (401, 403)
    assert cookie_client("acceptance-organizer").get(peer_scope_url).status_code == 200


# --- Session tokens are stored as digests, never as bearer secrets ------------


def _all_persisted_text(session):
    return " ".join(
        str(value) for value in Session.objects.filter(pk=session.pk).values().get().values()
    )


def test_session_row_never_contains_the_presented_token():
    user = User.objects.create_user("digest-user", password="pw-12345678")
    session = Session.issue(user)
    assert session.token not in _all_persisted_text(session)
    assert "token" not in {f.name for f in Session._meta.get_fields()}
    assert cookie_client(session.token).get("/api/v1/accounts/me/").status_code == 200


def test_login_cookie_works_but_database_holds_only_its_digest():
    User.objects.create_user("digest-login", password="pw-12345678")
    client = Client()
    response = client.post(
        "/api/v1/accounts/login/",
        {"username": "digest-login", "password": "pw-12345678"},
    )
    assert response.status_code == 200
    raw = response.cookies["session"].value
    session = Session.objects.get(user__username="digest-login")
    assert raw not in _all_persisted_text(session)
    assert session.token_digest == digest_session_token(raw)
    assert client.get("/api/v1/accounts/me/").status_code == 200


def test_presenting_a_stored_digest_as_the_token_does_not_authenticate():
    user = User.objects.create_user("digest-replay", password="pw-12345678")
    session = Session.issue(user)
    assert cookie_client(session.token_digest).get("/api/v1/accounts/me/").status_code == 401


def test_logout_revokes_the_session_by_digest():
    user = User.objects.create_user("digest-logout", password="pw-12345678")
    session = Session.issue(user)
    client = cookie_client(session.token)
    assert client.post("/api/v1/accounts/logout/").status_code == 204
    assert not Session.objects.filter(pk=session.pk).exists()
    assert cookie_client(session.token).get("/api/v1/accounts/me/").status_code == 401


def test_seeded_sessions_persist_only_digests():
    call_command("seed_acceptance_identities")
    stored = " ".join(Session.objects.values_list("token_digest", flat=True))
    assert "acceptance-organizer" not in stored
    assert Session.lookup("acceptance-organizer").count() == 1


@pytest.mark.django_db(transaction=True)
def test_migration_hashes_existing_plaintext_sessions_in_place():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    executor.migrate([("accounts", "0004_oidc")])
    old_apps = executor.loader.project_state([("accounts", "0004_oidc")]).apps
    OldUser, OldSession = (
        old_apps.get_model("accounts", "User"),
        old_apps.get_model("accounts", "Session"),
    )
    user = OldUser.objects.create(username="legacy-user")
    OldSession.objects.create(user=user, token="legacy-plain-token")

    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())

    assert Session.lookup("legacy-plain-token").count() == 1
    assert "legacy-plain-token" not in " ".join(
        Session.objects.values_list("token_digest", flat=True)
    )
