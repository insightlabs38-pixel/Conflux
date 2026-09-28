import base64
import hashlib
import json
import time
import urllib.parse
from datetime import timedelta

import jwt
import pytest
from accounts import oidc
from accounts.models import ExternalIdentity, OidcLoginState, Session, User
from audit.models import AuditEvent
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import Client
from django.utils import timezone
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ISSUER = "https://idp.example.test"
CLIENT_ID = "conflux-client"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwk(key, kid="k1"):
    data = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    return {**data, "kid": kid, "use": "sig", "alg": "RS256"}


class Provider:
    def __init__(self):
        self.calls = []
        self.claims = {}
        self.sign_with = KEY
        self.alg = "RS256"
        self.issuer_in_metadata = ISSUER

    def id_token(self, nonce, **overrides):
        now = int(time.time())
        claims = {
            "iss": ISSUER,
            "aud": CLIENT_ID,
            "sub": "subject-1",
            "iat": now,
            "exp": now + 300,
            "nonce": nonce,
            "email": "ada@example.test",
            "email_verified": True,
            "name": "Ada",
            **self.claims,
            **overrides,
        }
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, self.sign_with, algorithm=self.alg, headers={"kid": "k1"})

    def http_json(self, url, *, data=None, headers=None):
        self.calls.append((url, data, headers))
        if url.endswith("/.well-known/openid-configuration"):
            return {
                "issuer": self.issuer_in_metadata,
                "authorization_endpoint": ISSUER + "/authorize",
                "token_endpoint": ISSUER + "/token",
                "jwks_uri": ISSUER + "/jwks",
            }
        if url.endswith("/jwks"):
            return {"keys": [jwk(KEY)]}
        if url.endswith("/token"):
            return {"id_token": self.id_token(self.nonce), "access_token": "unused"}
        raise AssertionError(url)


@pytest.fixture
def idp(monkeypatch, settings):
    provider = Provider()
    provider.nonce = None
    settings.OIDC_ISSUER = ISSUER
    settings.OIDC_CLIENT_ID = CLIENT_ID
    settings.OIDC_CLIENT_SECRET = "s3cret"
    settings.OIDC_REDIRECT_URI = ""
    oidc._discovery_cache.clear()
    monkeypatch.setattr(oidc, "http_json", provider.http_json)
    return provider


def start(client, provider, next_path="/dashboard"):
    response = client.get("/api/v1/accounts/oidc/login/", {"next": next_path})
    assert response.status_code == 302
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(response["Location"]).query))
    provider.nonce = query["nonce"]
    return response, query


def finish(client, query, code="auth-code"):
    return client.get("/api/v1/accounts/oidc/callback/", {"code": code, "state": query["state"]})


def sign_in(idp, client=None, **kwargs):
    client = client or Client()
    _, query = start(client, idp, **kwargs)
    return client, finish(client, query)


def test_sso_is_off_by_default_and_local_login_is_untouched():
    client = Client()
    assert client.get("/api/v1/accounts/oidc/config/").json() == {"enabled": False}
    assert client.get("/api/v1/accounts/oidc/login/").status_code == 404
    assert (
        client.get("/api/v1/accounts/oidc/callback/", {"code": "x", "state": "y"}).status_code
        == 404
    )
    User.objects.create_user(username="local", password="pw-12345")
    login = client.post(
        "/api/v1/accounts/login/",
        {"username": "local", "password": "pw-12345"},
        content_type="application/json",
    )
    assert login.status_code == 200 and "session" in login.cookies


def test_config_never_contacts_the_provider(idp, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("network used")

    monkeypatch.setattr(oidc, "http_json", boom)
    body = Client().get("/api/v1/accounts/oidc/config/").json()
    assert body["enabled"] is True and body["login_url"] == "/api/v1/accounts/oidc/login/"


def test_authorization_request_uses_pkce_state_nonce_and_a_browser_binding(idp):
    client = Client()
    response, query = start(client, idp)
    assert response["Location"].startswith(ISSUER + "/authorize?")
    assert query["response_type"] == "code" and query["client_id"] == CLIENT_ID
    assert query["code_challenge_method"] == "S256"
    assert query["redirect_uri"].endswith("/api/v1/accounts/oidc/callback/")
    binder = response.cookies["oidc_binder"]
    assert binder["httponly"] and binder["samesite"] == "Lax"
    state = OidcLoginState.objects.get()
    assert state.state_hash != query["state"]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(state.code_verifier.encode()).digest())
    assert challenge.rstrip(b"=").decode() == query["code_challenge"]


def test_successful_sign_in_creates_a_password_less_user_and_session(idp):
    client, response = sign_in(idp)
    assert response.status_code == 302 and response["Location"] == "/dashboard"
    user = User.objects.get()
    assert user.username.startswith("oidc-") and not user.has_usable_password()
    assert user.email == "ada@example.test" and user.first_name == "Ada"
    assert ExternalIdentity.objects.get().subject == "subject-1"
    session_cookie = response.cookies["session"]
    assert (
        session_cookie["httponly"] and Session.objects.get(token=session_cookie.value).user == user
    )
    assert client.get("/api/v1/accounts/me/").json()["username"] == user.username
    assert AuditEvent.objects.filter(action="auth.oidc_login", actor=user).count() == 1
    assert not OidcLoginState.objects.exists()
    token_call = next(c for c in idp.calls if c[0].endswith("/token"))
    assert token_call[1]["grant_type"] == "authorization_code" and token_call[1]["code_verifier"]
    assert token_call[2]["Authorization"].startswith("Basic ")
    assert "client_secret" not in token_call[1]


def test_signing_in_again_reuses_the_same_account(idp):
    sign_in(idp)
    sign_in(idp)
    assert User.objects.count() == 1 and ExternalIdentity.objects.get().last_login_at


def test_state_is_single_use_and_bound_to_the_starting_browser(idp):
    client = Client()
    _, query = start(client, idp)
    stranger = Client()
    assert finish(stranger, query).status_code == 400
    assert not User.objects.exists()
    _, query = start(client, idp)
    assert finish(client, query).status_code == 302
    assert finish(client, query).status_code == 400
    assert (
        client.get("/api/v1/accounts/oidc/callback/", {"code": "x", "state": "nope"}).status_code
        == 400
    )
    assert User.objects.count() == 1


def test_an_expired_attempt_is_refused(idp):
    client = Client()
    _, query = start(client, idp)
    OidcLoginState.objects.update(created_at=timezone.now() - timedelta(minutes=11))
    assert finish(client, query).status_code == 400 and not User.objects.exists()


@pytest.mark.parametrize(
    "case",
    ["nonce", "audience", "issuer", "expired", "other_key", "hs256", "no_exp", "no_sub", "azp"],
)
def test_invalid_identity_tokens_never_create_users_or_sessions(idp, case):
    if case == "nonce":
        idp.claims = {"nonce": "attacker"}
    elif case == "audience":
        idp.claims = {"aud": "someone-else"}
    elif case == "issuer":
        idp.claims = {"iss": "https://evil.test"}
    elif case == "expired":
        idp.claims = {"exp": int(time.time()) - 3600, "iat": int(time.time()) - 7200}
    elif case == "other_key":
        idp.sign_with = OTHER_KEY
    elif case == "hs256":
        idp.alg, idp.sign_with = "HS256", "shared-secret-that-is-long-enough-0123456789"
    elif case == "no_exp":
        idp.claims = {"exp": None}
    elif case == "no_sub":
        idp.claims = {"sub": ""}
    elif case == "azp":
        idp.claims = {"aud": [CLIENT_ID, "other"], "azp": "other"}
    client, response = sign_in(idp)
    assert response.status_code == 400
    assert "session" not in response.cookies
    assert not User.objects.exists() and not Session.objects.exists()


def test_provider_errors_and_a_hostile_discovery_document_are_refused(idp):
    client = Client()
    _, query = start(client, idp)
    assert (
        client.get(
            "/api/v1/accounts/oidc/callback/", {"error": "access_denied", "state": query["state"]}
        ).status_code
        == 400
    )
    oidc._discovery_cache.clear()
    idp.issuer_in_metadata = "https://evil.test"
    assert Client().get("/api/v1/accounts/oidc/login/").status_code == 502


def test_plain_http_providers_are_refused_unless_explicitly_allowed(settings):
    with pytest.raises(oidc.OidcError):
        oidc._check_url("http://idp.example.test/token")
    settings.OIDC_ALLOW_INSECURE_HTTP = True
    oidc._check_url("http://idp.example.test/token")
    with pytest.raises(oidc.OidcError):
        oidc._check_url("file:///etc/passwd")


def test_email_domain_allowlist_requires_a_verified_address(idp, settings):
    settings.OIDC_ALLOWED_EMAIL_DOMAINS = ["corp.test"]
    assert sign_in(idp)[1].status_code == 400
    idp.claims = {"email": "ada@corp.test", "email_verified": False}
    assert sign_in(idp)[1].status_code == 400
    idp.claims = {"email": "ada@corp.test", "email_verified": True}
    assert sign_in(idp)[1].status_code == 302
    assert User.objects.count() == 1


def test_existing_local_accounts_are_not_linked_by_email_unless_opted_in(idp, settings):
    local = User.objects.create_user(username="ada", email="ada@example.test", password="pw-12345")
    sign_in(idp)
    assert ExternalIdentity.objects.get().user != local and User.objects.count() == 2
    User.objects.filter(username__startswith="oidc-").delete()
    settings.OIDC_LINK_BY_VERIFIED_EMAIL = True
    idp.claims = {"email_verified": False, "sub": "s2"}
    sign_in(idp)
    assert ExternalIdentity.objects.get(subject="s2").user != local
    idp.claims = {"sub": "s3"}
    sign_in(idp)
    assert ExternalIdentity.objects.get(subject="s3").user == local


def test_auto_creation_can_be_disabled(idp, settings):
    settings.OIDC_AUTO_CREATE_USERS = False
    assert sign_in(idp)[1].status_code == 400 and not User.objects.exists()


def test_default_workspace_membership_is_participant_only(idp, settings):
    workspace = Workspace.objects.create(name="W", slug="w")
    settings.OIDC_DEFAULT_WORKSPACE_SLUG = "w"
    sign_in(idp)
    assert Membership.objects.get(workspace=workspace).role == Role.PARTICIPANT


def test_disabled_accounts_cannot_sign_in(idp):
    sign_in(idp)
    User.objects.update(is_active=False)
    assert sign_in(idp)[1].status_code == 400


@pytest.mark.parametrize(
    "target", ["//evil.test", "https://evil.test/x", "/\\evil.test", "javascript:1", "/ok/path?x=1"]
)
def test_return_path_is_restricted_to_the_same_site(idp, target):
    _, response = sign_in(idp, next_path=target)
    assert response["Location"] == (target if target == "/ok/path?x=1" else "/")
