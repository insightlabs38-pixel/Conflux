from audit.services import record_mutation
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import oidc
from .models import ExternalIdentity
from .views import start_session


BINDER_COOKIE = "oidc_binder"


class OidcConfigSchema(serializers.Serializer):
    enabled = serializers.BooleanField()
    provider_name = serializers.CharField(required=False)
    login_url = serializers.CharField(required=False)


def _disabled():
    return Response({"detail": "Single sign-on is not configured."}, status=404)


@extend_schema(responses=OidcConfigSchema)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def oidc_config(request):
    if not oidc.enabled():
        return Response({"enabled": False})
    return Response(
        {
            "enabled": True,
            "provider_name": settings.OIDC_PROVIDER_NAME,
            "login_url": "/api/v1/accounts/oidc/login/",
        }
    )


@extend_schema(
    parameters=[OpenApiParameter("next", str, description="Same-site path to return to.")],
    responses={302: None},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def oidc_login(request):
    if not oidc.enabled():
        return _disabled()
    try:
        url, binder = oidc.begin(request, request.query_params.get("next", "/"))
    except oidc.OidcError as exc:
        return Response({"detail": str(exc)}, status=502)
    response = HttpResponseRedirect(url)
    response.set_cookie(
        BINDER_COOKIE,
        binder,
        max_age=int(oidc.STATE_TTL.total_seconds()),
        httponly=True,
        samesite="Lax",
        secure=request.is_secure() or request.META.get("HTTP_X_FORWARDED_PROTO") == "https",
        path="/api/v1/accounts/oidc/",
    )
    return response


@extend_schema(
    parameters=[
        OpenApiParameter("code", str),
        OpenApiParameter("state", str),
        OpenApiParameter("error", str),
    ],
    responses={302: None},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def oidc_callback(request):
    if not oidc.enabled():
        return _disabled()
    if request.query_params.get("error"):
        return Response({"detail": "The identity provider declined the sign-in."}, status=400)
    try:
        claims, next_path = oidc.exchange(
            request,
            request.query_params.get("code"),
            request.query_params.get("state"),
            request.COOKIES.get(BINDER_COOKIE),
        )
        with transaction.atomic():
            user = oidc.resolve_user(claims)
            record_mutation(
                actor=user,
                workspace=None,
                action="auth.oidc_login",
                target=ExternalIdentity.objects.get(
                    issuer=settings.OIDC_ISSUER, subject=claims["sub"]
                ),
                metadata={"issuer": settings.OIDC_ISSUER},
            )
    except oidc.OidcError as exc:
        return Response({"detail": str(exc)}, status=400)
    response = start_session(request, user, HttpResponseRedirect(next_path))
    response.delete_cookie(BINDER_COOKIE, path="/api/v1/accounts/oidc/")
    return response
