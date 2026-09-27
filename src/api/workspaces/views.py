from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import record_mutation
from core.idempotency import IdempotentMixin
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership, Role, Workspace
from .serializers import (
    MembershipInputSchema,
    MembershipSchema,
    WorkspaceInputSchema,
    WorkspaceSchema,
)


def _serialize_workspace(workspace):
    return {"public_id": str(workspace.public_id), "name": workspace.name, "slug": workspace.slug}


def _serialize_membership(membership):
    return {
        "public_id": str(membership.public_id),
        "user": membership.user.username,
        "role": membership.role,
    }


class WorkspaceCreateView(IdempotentMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=WorkspaceInputSchema, responses={201: WorkspaceSchema})
    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "name is required."}, status=400)
        slug = (request.data.get("slug") or slugify(name)).strip()

        try:
            with transaction.atomic():
                workspace = Workspace.objects.create(name=name, slug=slug)
                Membership.objects.create(
                    user=request.user, workspace=workspace, role=Role.ORGANIZER
                )
                record_mutation(
                    actor=request.user,
                    workspace=workspace,
                    action="workspace.created",
                    target=workspace,
                    event_type="workspace.created",
                    payload={"workspace": str(workspace.public_id), "name": name},
                )
        except IntegrityError:
            return Response({"detail": "A workspace with that slug already exists."}, status=409)

        return Response(_serialize_workspace(workspace), status=201)


class WorkspaceMembersView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=MembershipSchema(many=True))
    def get(self, request, workspace_public_id):
        members = Membership.objects.filter(workspace=self.get_workspace()).select_related("user")
        return Response([_serialize_membership(m) for m in members])

    @extend_schema(
        request=MembershipInputSchema, responses={200: MembershipSchema, 201: MembershipSchema}
    )
    def post(self, request, workspace_public_id):
        workspace = self.get_workspace()
        username = request.data.get("username")
        role = request.data.get("role")
        if role not in Role.values:
            return Response({"detail": f"role must be one of {Role.values}."}, status=400)
        user = get_object_or_404(User, username=username)

        with transaction.atomic():
            membership, created = Membership.objects.get_or_create(
                user=user, workspace=workspace, role=role
            )
            if created:
                record_mutation(
                    actor=request.user,
                    workspace=workspace,
                    action="membership.granted",
                    target=membership,
                    event_type="membership.granted",
                    payload={"user": user.username, "role": role},
                )
        return Response(_serialize_membership(membership), status=201 if created else 200)
