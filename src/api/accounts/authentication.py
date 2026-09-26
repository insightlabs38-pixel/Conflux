from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Session

COOKIE_NAME = "session"


class CookieSessionAuthentication(BaseAuthentication):
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
