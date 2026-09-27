from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import record_mutation
from core.authz import has_any_role
from core.mixins import WorkspaceLookupMixin
from core.permissions import IsWorkspaceMember
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Membership, Role

from .expertise import normalize_tag
from .models import JudgeExpertiseProfile


class ExpertiseInputSchema(serializers.Serializer):
    tags = serializers.ListField(child=serializers.CharField(max_length=80), max_length=20)

    def validate_tags(self, tags):
        normalized = [normalize_tag(tag) for tag in tags]
        if any(not tag or any(ord(char) < 32 for char in tag) for tag in normalized):
            raise serializers.ValidationError(
                "Tags must be nonempty text without control characters."
            )
        if len(set(normalized)) != len(normalized):
            raise serializers.ValidationError("Tags must be unique, ignoring case.")
        return sorted(normalized)


class ExpertiseOutputSchema(serializers.Serializer):
    judge = serializers.UUIDField()
    tags = serializers.ListField(child=serializers.CharField())
    updated_at = serializers.DateTimeField(allow_null=True)


class JudgeExpertiseView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def target(self, judge_public_id=None):
        if judge_public_id is None:
            judge = self.request.user
        else:
            judge = get_object_or_404(
                User.objects.filter(
                    memberships__workspace=self.get_workspace(), memberships__role=Role.JUDGE
                ).distinct(),
                public_id=judge_public_id,
            )
        if not Membership.objects.filter(
            workspace=self.get_workspace(), user=judge, role=Role.JUDGE
        ).exists():
            raise PermissionDenied("This user is not a judge in the workspace.")
        if judge.id != self.request.user.id and not has_any_role(
            self.request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN
        ):
            raise PermissionDenied("Only organizers can edit another judge's expertise.")
        return judge

    @extend_schema(responses=ExpertiseOutputSchema)
    def get(self, request, workspace_public_id, judge_public_id=None):
        judge = self.target(judge_public_id)
        profile = JudgeExpertiseProfile.objects.filter(
            workspace=self.get_workspace(), judge=judge
        ).first()
        return Response(
            {
                "judge": str(judge.public_id),
                "tags": profile.tags if profile else [],
                "updated_at": profile.updated_at if profile else None,
            }
        )

    @extend_schema(request=ExpertiseInputSchema, responses=ExpertiseOutputSchema)
    def put(self, request, workspace_public_id, judge_public_id=None):
        judge = self.target(judge_public_id)
        serializer = ExpertiseInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        tags = serializer.validated_data["tags"]
        with transaction.atomic():
            profile, _ = JudgeExpertiseProfile.objects.select_for_update().get_or_create(
                workspace=self.get_workspace(), judge=judge
            )
            if profile.tags != tags:
                profile.tags = tags
                profile.save(update_fields=["tags", "updated_at"])
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="judge_expertise.updated",
                    target=profile,
                    metadata={"judge": str(judge.public_id), "tags": tags},
                )
        return Response(
            {"judge": str(judge.public_id), "tags": profile.tags, "updated_at": profile.updated_at}
        )
