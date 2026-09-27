import re
import secrets
from datetime import timedelta
from uuid import UUID

from audit.services import record_mutation
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from events.models import Event
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .authentication import CookieOnlyAuthentication
from .models import ApiCredential, digest_api_token

ACTION_PATTERN = re.compile(r"^(GET|POST|PATCH|PUT|DELETE):[a-z0-9-]+$")


def _serialize(credential):
    return {
        "public_id": str(credential.public_id),
        "name": credential.name,
        "workspace": str(credential.workspace.public_id),
        "event": str(credential.event.public_id) if credential.event else None,
        "allowed_actions": credential.allowed_actions,
        "created_at": credential.created_at,
        "expires_at": credential.expires_at,
        "revoked_at": credential.revoked_at,
    }


class CredentialView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieOnlyAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id):
        credentials = (
            ApiCredential.objects.filter(workspace=self.get_workspace())
            .select_related("workspace", "event")
            .order_by("-created_at")
        )
        return Response([_serialize(item) for item in credentials])

    def post(self, request, workspace_public_id):
        name = request.data.get("name")
        actions = request.data.get("allowed_actions")
        days = request.data.get("expires_in_days", 30)
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            raise ValidationError({"name": "Enter a name of 1 to 120 characters."})
        if (
            not isinstance(actions, list)
            or not 1 <= len(actions) <= 50
            or any(
                not isinstance(value, str) or not ACTION_PATTERN.fullmatch(value)
                for value in actions
            )
            or len(actions) != len(set(actions))
        ):
            raise ValidationError(
                {"allowed_actions": "Enter 1 to 50 unique METHOD:route-name actions."}
            )
        if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 90:
            raise ValidationError({"expires_in_days": "Must be an integer from 1 to 90."})
        event_id = request.data.get("event")
        event = None
        if event_id is not None:
            try:
                event_uuid = UUID(str(event_id))
            except (ValueError, TypeError) as exc:
                raise ValidationError({"event": "Enter a valid event public ID."}) from exc
            event = get_object_or_404(Event, public_id=event_uuid, workspace=self.get_workspace())
        raw_token = secrets.token_urlsafe(32)
        with transaction.atomic():
            credential = ApiCredential.objects.create(
                workspace=self.get_workspace(),
                event=event,
                owner=request.user,
                name=name.strip(),
                token_digest=digest_api_token(raw_token),
                allowed_actions=actions,
                expires_at=timezone.now() + timedelta(days=days),
            )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="api_credential.issued",
                target=credential,
                metadata={"event_id": str(event.public_id) if event else None, "actions": actions},
            )
        return Response({**_serialize(credential), "token": raw_token}, status=201)


class CredentialRevokeView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieOnlyAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def post(self, request, workspace_public_id, credential_public_id):
        with transaction.atomic():
            credential = get_object_or_404(
                ApiCredential.objects.select_for_update().select_related("workspace", "event"),
                workspace=self.get_workspace(),
                public_id=credential_public_id,
            )
            if credential.revoked_at is not None:
                raise ValidationError({"detail": "Credential is already revoked."})
            credential.revoked_at = timezone.now()
            credential.save(update_fields=["revoked_at"])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="api_credential.revoked",
                target=credential,
            )
        return Response(_serialize(credential))
