"""The read-only preview endpoint (PREVIEW_CONTEXT, PD-F002-B03-T01): resolves, stores nothing."""

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from . import preview_context
from .mixins import WorkspaceLookupMixin
from .permissions import require_roles


class PreviewContextInputSchema(serializers.Serializer):
    role = serializers.CharField(required=False, allow_null=True)
    at = serializers.CharField(required=False, allow_null=True, help_text="ISO time with offset.")
    version = serializers.CharField(required=False, allow_null=True)


class PreviewAsInputSchema(serializers.Serializer):
    ref = serializers.DictField(child=serializers.CharField(), required=False)
    context = PreviewContextInputSchema(required=False)
    input = serializers.JSONField(required=False)


class PreviewVersionSchema(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    at = serializers.CharField(allow_null=True)
    by = serializers.CharField(allow_null=True)
    current = serializers.BooleanField()


class PreviewResolvedSchema(serializers.Serializer):
    role = serializers.CharField(allow_null=True)
    at = serializers.CharField(allow_null=True)
    version = PreviewVersionSchema(allow_null=True)
    live = serializers.BooleanField()


class PreviewNoticeSchema(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class PreviewAsSchema(serializers.Serializer):
    surface = serializers.CharField()
    label = serializers.CharField()
    summary = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField())
    versions = PreviewVersionSchema(many=True)
    resolved = PreviewResolvedSchema()
    notices = PreviewNoticeSchema(many=True)
    data = serializers.JSONField(help_text="The surface's own payload.")


class PreviewAsView(WorkspaceLookupMixin, APIView):
    """Organizers and admins resolve what someone else would see; nothing is saved or sent."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(request=PreviewAsInputSchema, responses=PreviewAsSchema)
    def post(self, request, workspace_public_id, surface):
        found = preview_context.SURFACES.get(surface)
        if found is None:
            raise NotFound()
        body = request.data if isinstance(request.data, dict) else {}
        ref = body.get("ref") or {}
        if not isinstance(ref, dict):
            raise ValidationError({"ref": ["Send the reference as an object."]})
        missing = [n for n in found.params if not isinstance(ref.get(n), str) or not ref[n]]
        if missing:
            raise ValidationError({f"ref.{n}": ["This value is required."] for n in missing})
        try:
            answer = preview_context.preview(
                surface,
                request.user,
                self.get_workspace(),
                {n: ref[n] for n in found.params},
                body.get("context"),
                body.get("input"),
            )
        except preview_context.PreviewError as error:
            raise ValidationError(error.problems) from error
        except preview_context.NotVisible as error:
            raise NotFound() from error
        response = Response(answer.as_dict())
        response["Cache-Control"] = "private, no-store"
        return response
