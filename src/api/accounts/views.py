from datetime import timedelta

from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .authentication import COOKIE_NAME, CookieSessionAuthentication
from .models import Session

SESSION_TTL = timedelta(hours=12)


def _serialize_user(user):
    from workspaces.models import Membership

    memberships = Membership.objects.filter(user=user).select_related("workspace")
    return {
        "public_id": str(user.public_id),
        "username": user.username,
        "memberships": [
            {
                "workspace": str(m.workspace.public_id),
                "workspace_name": m.workspace.name,
                "workspace_slug": m.workspace.slug,
                "role": m.role,
            }
            for m in memberships
        ],
    }


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=401)
    session = Session.issue(user, ttl=SESSION_TTL)
    response = Response({"user": _serialize_user(user)})
    response.set_cookie(COOKIE_NAME, session.token, httponly=True, samesite="Lax")
    return response


@api_view(["POST"])
@authentication_classes([CookieSessionAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    token = request.COOKIES.get(COOKIE_NAME)
    if token:
        Session.objects.filter(token=token).delete()
    response = Response(status=204)
    response.delete_cookie(COOKIE_NAME)
    return response


@api_view(["GET"])
@authentication_classes([CookieSessionAuthentication])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(_serialize_user(request.user))
