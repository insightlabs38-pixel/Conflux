from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import ApiCredential, Session, digest_api_token

COOKIE_NAME = "session"


class CookieOnlyAuthentication(BaseAuthentication):
    """Resolves a user from the `session` cookie.

    The acceptance checker never logs in; it attaches a pre-issued cookie
    directly (see `.dogfood.toml`), so authentication has to work from that
    cookie alone with no CSRF/session-middleware handshake beforehand.
    """

    def authenticate(self, request):
        token = request.COOKIES.get(COOKIE_NAME)
        if not token:
            return None
        try:
            session = Session.objects.select_related("user").get(token=token)
        except Session.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid session.") from exc
        if session.is_expired():
            raise AuthenticationFailed("Session expired.")
        if not session.user.is_active:
            raise AuthenticationFailed("Account disabled.")
        return (session.user, session)

    def authenticate_header(self, request):
        # Presence of this makes DRF return 401 (not 403) when no/invalid
        # cookie is supplied, matching the checker's "401 or 403" tolerance
        # while giving the stricter of the two by default.
        return 'Cookie realm="session"'


class CookieSessionAuthentication(CookieOnlyAuthentication):
    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            return super().authenticate(request)
        scheme, separator, token = header.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token or " " in token:
            raise AuthenticationFailed("Invalid API credential.")
        credential = (
            ApiCredential.objects.select_related("owner", "workspace", "event")
            .filter(token_digest=digest_api_token(token))
            .first()
        )
        if credential is None or not credential.is_active():
            raise AuthenticationFailed("Invalid API credential.")
        match = request._request.resolver_match
        kwargs = match.kwargs if match else {}
        if str(kwargs.get("workspace_public_id", "")) != str(credential.workspace.public_id):
            raise AuthenticationFailed("API credential is outside its workspace scope.")
        if credential.event_id and str(kwargs.get("event_public_id", "")) != str(
            credential.event.public_id
        ):
            raise AuthenticationFailed("API credential is outside its event scope.")
        method = "GET" if request.method == "HEAD" else request.method
        action = f"{method}:{match.url_name}" if match and match.url_name else ""
        if action not in credential.allowed_actions:
            raise AuthenticationFailed("API credential does not allow this action.")
        return credential.owner, credential

    def authenticate_header(self, request):
        return (
            'Bearer realm="api"'
            if request.META.get("HTTP_AUTHORIZATION")
            else super().authenticate_header(request)
        )
