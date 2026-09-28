"""Generic OpenID Connect authorization-code sign-in with PKCE.

Deliberately dependency-free beyond PyJWT: discovery, token exchange and JWKS
retrieval use the standard library with short timeouts, and every network call
happens lazily inside a sign-in request.
"""

import base64
import hashlib
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

import jwt
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import ExternalIdentity, OidcLoginState, User

STATE_TTL = timedelta(minutes=10)
ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "PS256", "EdDSA"]
MAX_BODY = 1024 * 1024
CLOCK_SKEW = 60
_DISCOVERY_TTL = 3600
_discovery_cache = {}


class OidcError(Exception):
    """A failed or refused sign-in; the message is safe to show the user."""


def enabled():
    return bool(settings.OIDC_ISSUER and settings.OIDC_CLIENT_ID)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _check_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme == "https" or (parts.scheme == "http" and settings.OIDC_ALLOW_INSECURE_HTTP):
        return
    raise OidcError("The identity provider must be reached over https.")


def http_json(url, *, data=None, headers=None):
    """GET, or form POST when `data` is given. Isolated so tests can stand in a provider."""
    _check_url(url)
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, headers=headers or {})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=5) as response:
            raw = response.read(MAX_BODY + 1)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise OidcError("The identity provider could not be reached.") from exc
    if len(raw) > MAX_BODY:
        raise OidcError("The identity provider sent an oversized response.")
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise OidcError("The identity provider sent an invalid response.") from exc


def discovery():
    cached = _discovery_cache.get(settings.OIDC_ISSUER)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    doc = http_json(settings.OIDC_ISSUER + "/.well-known/openid-configuration")
    if str(doc.get("issuer", "")).rstrip("/") != settings.OIDC_ISSUER:
        raise OidcError("The identity provider reported an unexpected issuer.")
    for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        if not isinstance(doc.get(key), str):
            raise OidcError("The identity provider metadata is incomplete.")
        _check_url(doc[key])
    _discovery_cache[settings.OIDC_ISSUER] = (time.monotonic() + _DISCOVERY_TTL, doc)
    return doc


def redirect_uri(request):
    return settings.OIDC_REDIRECT_URI or request.build_absolute_uri(
        "/api/v1/accounts/oidc/callback/"
    )


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def safe_next(value):
    """Only same-site absolute paths; anything else falls back to the root."""
    if (
        isinstance(value, str)
        and value.startswith("/")
        and not value.startswith("//")
        and "\\" not in value
        and "\n" not in value
        and "\r" not in value
        and len(value) <= 500
    ):
        return value
    return "/"


def begin(request, next_path="/"):
    meta = discovery()
    state = secrets.token_urlsafe(32)
    binder = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    OidcLoginState.objects.filter(created_at__lt=timezone.now() - STATE_TTL).delete()
    OidcLoginState.objects.create(
        state_hash=_digest(state),
        browser_hash=_digest(binder),
        nonce=nonce,
        code_verifier=verifier,
        next_path=safe_next(next_path),
    )
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")
    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": settings.OIDC_CLIENT_ID,
            "redirect_uri": redirect_uri(request),
            "scope": settings.OIDC_SCOPES,
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge.decode(),
            "code_challenge_method": "S256",
        }
    )
    separator = "&" if "?" in meta["authorization_endpoint"] else "?"
    return meta["authorization_endpoint"] + separator + query, binder


def _consume_state(state, binder):
    with transaction.atomic():
        row = (
            OidcLoginState.objects.select_for_update()
            .filter(state_hash=_digest(state or ""))
            .first()
        )
        if row is None:
            raise OidcError("This sign-in attempt is unknown or has already been used.")
        row.delete()
    if not binder or not secrets.compare_digest(row.browser_hash, _digest(binder)):
        raise OidcError("This sign-in attempt was not started in this browser.")
    if row.created_at < timezone.now() - STATE_TTL:
        raise OidcError("This sign-in attempt has expired.")
    return row


def _verify_id_token(id_token, meta, nonce):
    try:
        header = jwt.get_unverified_header(id_token)
    except jwt.PyJWTError as exc:
        raise OidcError("The identity token is malformed.") from exc
    if header.get("alg") not in ALLOWED_ALGORITHMS:
        raise OidcError("The identity token uses an unsupported signature algorithm.")
    jwks = http_json(meta["jwks_uri"])
    keys = [k for k in jwks.get("keys", []) if isinstance(k, dict)]
    kid = header.get("kid")
    candidates = [k for k in keys if kid is None or k.get("kid") == kid]
    for candidate in candidates:
        try:
            key = jwt.PyJWK.from_dict(candidate).key
            claims = jwt.decode(
                id_token,
                key,
                algorithms=[header["alg"]],
                audience=settings.OIDC_CLIENT_ID,
                issuer=settings.OIDC_ISSUER,
                leeway=CLOCK_SKEW,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.InvalidSignatureError:
            continue
        except (jwt.PyJWTError, ValueError) as exc:
            raise OidcError("The identity token was rejected.") from exc
        break
    else:
        raise OidcError("The identity token signature could not be verified.")
    if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
        raise OidcError("The identity token does not match this sign-in attempt.")
    audience = claims["aud"]
    if (
        isinstance(audience, list)
        and len(audience) > 1
        and claims.get("azp") != settings.OIDC_CLIENT_ID
    ):
        raise OidcError("The identity token was issued to a different client.")
    if not isinstance(claims["sub"], str) or not claims["sub"] or len(claims["sub"]) > 255:
        raise OidcError("The identity token has no usable subject.")
    return claims


def exchange(request, code, state, binder):
    row = _consume_state(state, binder)
    if not isinstance(code, str) or not code:
        raise OidcError("The provider did not return an authorization code.")
    meta = discovery()
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri(request),
        "client_id": settings.OIDC_CLIENT_ID,
        "code_verifier": row.code_verifier,
    }
    headers = {"Accept": "application/json"}
    if settings.OIDC_CLIENT_SECRET:
        credentials = ":".join(
            urllib.parse.quote(value, safe="")
            for value in (settings.OIDC_CLIENT_ID, settings.OIDC_CLIENT_SECRET)
        )
        headers["Authorization"] = "Basic " + base64.b64encode(credentials.encode()).decode()
    tokens = http_json(meta["token_endpoint"], data=form, headers=headers)
    id_token = tokens.get("id_token")
    if not isinstance(id_token, str):
        raise OidcError("The provider did not return an identity token.")
    return _verify_id_token(id_token, meta, row.nonce), row.next_path


def _email_allowed(email):
    domains = settings.OIDC_ALLOWED_EMAIL_DOMAINS
    if not domains:
        return True
    return "@" in email and email.rsplit("@", 1)[1].lower() in domains


def _new_username(subject):
    digest = _digest(f"{settings.OIDC_ISSUER}|{subject}")[:20]
    return f"oidc-{digest}"


def resolve_user(claims):
    """Map verified claims to a local user, creating or linking only as configured."""
    subject = claims["sub"]
    email = str(claims.get("email", ""))[:254] if isinstance(claims.get("email", ""), str) else ""
    verified = claims.get("email_verified") is True
    if not _email_allowed(email if verified else ""):
        raise OidcError("Your email address is not allowed to sign in here.")
    identity = (
        ExternalIdentity.objects.select_related("user")
        .filter(issuer=settings.OIDC_ISSUER, subject=subject)
        .first()
    )
    if identity is None:
        user = None
        if settings.OIDC_LINK_BY_VERIFIED_EMAIL and verified and email:
            matches = list(User.objects.filter(email__iexact=email, is_active=True)[:2])
            if len(matches) == 1:
                user = matches[0]
        if user is None:
            if not settings.OIDC_AUTO_CREATE_USERS:
                raise OidcError("No account is linked to this identity.")
            user = _create_user(subject, email if verified else "", claims)
        try:
            with transaction.atomic():
                identity = ExternalIdentity.objects.create(
                    user=user, issuer=settings.OIDC_ISSUER, subject=subject, email=email
                )
        except IntegrityError:
            identity = ExternalIdentity.objects.select_related("user").get(
                issuer=settings.OIDC_ISSUER, subject=subject
            )
    if not identity.user.is_active:
        raise OidcError("This account is disabled.")
    identity.last_login_at = timezone.now()
    identity.save(update_fields=["last_login_at"])
    return identity.user


def _create_user(subject, email, claims):
    from workspaces.models import Membership, Role, Workspace

    user = User(username=_new_username(subject), email=email)
    name = claims.get("name")
    if isinstance(name, str):
        user.first_name = name[:150]
    user.set_unusable_password()
    try:
        with transaction.atomic():
            user.save()
    except IntegrityError:
        return User.objects.get(username=user.username)
    slug = settings.OIDC_DEFAULT_WORKSPACE_SLUG
    if slug:
        # Only the lowest-privilege role can be granted automatically; elevated roles
        # stay an organizer decision.
        workspace = Workspace.objects.filter(slug=slug).first()
        if workspace:
            Membership.objects.get_or_create(
                workspace=workspace, user=user, defaults={"role": Role.PARTICIPANT}
            )
    return user
