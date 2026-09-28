"""Event maintenance (read-only) mode.

While an event is read-only, every API write scoped to it is refused with 503 unless
the caller is an organizer/admin of the event's workspace. Enforced centrally after
each view's own permission checks, so a route cannot opt out by accident and
authorization failures (401/403/404) still take precedence.
"""

from core.authz import has_any_role
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import SAFE_METHODS
from rest_framework.views import APIView
from workspaces.models import Role

DEFAULT_MESSAGE = "This event is in maintenance mode and temporarily read-only."


class ReadOnlyMode(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "read_only"


def enforce(request, view):
    if request.method in SAFE_METHODS:
        return
    event_id = view.kwargs.get("event_public_id") if hasattr(view, "kwargs") else None
    if not event_id:
        return
    from .models import GovernanceSettings

    row = (
        GovernanceSettings.objects.select_related("event__workspace")
        .filter(event__public_id=event_id, read_only=True)
        .first()
    )
    if row is None:
        return
    user = request.user
    if getattr(user, "is_authenticated", False) and has_any_role(
        user, row.event.workspace, Role.ORGANIZER, Role.ADMIN
    ):
        return
    exc = ReadOnlyMode(row.read_only_message or DEFAULT_MESSAGE)
    exc.wait = 300
    raise exc


_original = APIView.check_permissions


def install():
    if getattr(APIView.check_permissions, "_maintenance_guard", False):
        return

    def check_permissions(self, request):
        _original(self, request)
        enforce(request, self)

    check_permissions._maintenance_guard = True
    APIView.check_permissions = check_permissions
