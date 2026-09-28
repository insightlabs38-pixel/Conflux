from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .authentication import COOKIE_NAME, CookieSessionAuthentication
from .models import LoginFailure, Session
from .serializers import LoginInputSchema, LoginResponseSchema, UserSummarySchema

SESSION_TTL = timedelta(hours=12)
LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)


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


@extend_schema(request=LoginInputSchema, responses={200: LoginResponseSchema})
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return Response({"detail": "Invalid credentials."}, status=401)
    key = username.strip().lower()[:150]
    cutoff = timezone.now() - LOGIN_FAILURE_WINDOW
    recent = LoginFailure.objects.filter(username=key, created_at__gte=cutoff)
    if recent.count() >= LOGIN_FAILURE_LIMIT:
        response = Response({"detail": "Too many failed attempts. Try again later."}, status=429)
        response["Retry-After"] = str(int(LOGIN_FAILURE_WINDOW.total_seconds()))
        return response
    user = authenticate(request, username=username, password=password)
    if user is None:
        LoginFailure.objects.create(username=key)
        LoginFailure.objects.filter(created_at__lt=cutoff - LOGIN_FAILURE_WINDOW).delete()
        return Response({"detail": "Invalid credentials."}, status=401)
    LoginFailure.objects.filter(username=key).delete()
    session = Session.issue(user, ttl=SESSION_TTL)
    response = Response({"user": _serialize_user(user)})
    secure = request.is_secure() or request.META.get("HTTP_X_FORWARDED_PROTO") == "https"
    response.set_cookie(
        COOKIE_NAME,
        session.token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="Lax",
        secure=secure,
    )
    return response


@extend_schema(request=None, responses={204: None})
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


@extend_schema(responses=UserSummarySchema)
@api_view(["GET"])
@authentication_classes([CookieSessionAuthentication])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(_serialize_user(request.user))
