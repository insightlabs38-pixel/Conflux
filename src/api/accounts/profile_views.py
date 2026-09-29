from audit.models import AuditEvent
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from workspaces.models import Membership

from .authentication import CookieSessionAuthentication
from .models import User, UserProfile
from .profile import identity_for
from .serializers import UserProfileSerializer


def _signals(user):
    from evaluations.models import JudgeExpertiseProfile
    from mentorship.models import MentorProfile
    from participation.models import MarketplaceProfile

    workspaces = Membership.objects.filter(user=user).values("workspace_id")
    market = MarketplaceProfile.objects.filter(
        user=user, event__workspace__in=workspaces
    ).select_related("event")
    judges = JudgeExpertiseProfile.objects.filter(judge=user, workspace__in=workspaces)
    mentors = (
        MentorProfile.objects.filter(mentor=user, event__workspace__in=workspaces)
        .select_related("event")
        .prefetch_related("track_expertise")
    )
    return {
        "event_profiles": [
            {
                "event": str(row.event.public_id),
                "event_name": row.event.name,
                "skills": row.skills,
                "roles": row.roles,
                "interests": row.interests,
                "team_seeking": row.visible,
                "availability_hours_per_week": row.availability_hours_per_week,
            }
            for row in market
        ],
        "judge_expertise": [
            {"workspace": str(row.workspace.public_id), "tags": row.tags}
            for row in judges.select_related("workspace")
        ],
        "mentoring": [
            {
                "event_name": row.event.name,
                "headline": row.headline,
                "available": row.is_available,
                "tracks": list(row.track_expertise.values_list("name", flat=True)),
            }
            for row in mentors
        ],
    }


@extend_schema(request=UserProfileSerializer, methods=["PATCH"])
@extend_schema(responses={200: {"type": "object"}})
@api_view(["GET", "PATCH"])
@authentication_classes([CookieSessionAuthentication])
@permission_classes([IsAuthenticated])
def my_profile(request):
    if request.method == "PATCH":
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            AuditEvent.objects.create(
                actor=request.user,
                action="account.profile_updated",
                target_type="accounts.userprofile",
                target_id=str(profile.public_id),
                metadata={"fields": sorted(serializer.validated_data)},
            )
    else:
        profile = UserProfile.objects.filter(user=request.user).first() or UserProfile(
            user=request.user
        )
    return Response(
        {
            **UserProfileSerializer(profile).data,
            **identity_for(request.user, viewer=request.user),
            **_signals(request.user),
        }
    )


@extend_schema(responses={200: {"type": "object"}})
@api_view(["GET"])
@authentication_classes([CookieSessionAuthentication])
@permission_classes([AllowAny])
def person_profile(request, user_public_id):
    user = get_object_or_404(User, public_id=user_public_id)
    profile = UserProfile.objects.filter(user=user).first()
    identity = identity_for(user, viewer=request.user if request.user.is_authenticated else None)
    if profile is None or (profile.visibility == "private" and request.user != user):
        return Response({"detail": "Not found."}, status=404)
    if profile.visibility == "members" and request.user != user:
        if (
            not request.user.is_authenticated
            or not Membership.objects.filter(
                user=user,
                workspace__in=Membership.objects.filter(user=request.user).values("workspace_id"),
            ).exists()
        ):
            return Response({"detail": "Not found."}, status=404)
    return Response(identity)
