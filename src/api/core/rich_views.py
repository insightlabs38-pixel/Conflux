"""The rich-content preview endpoint (PD-F002-B02-T02): renders for the caller, stores nothing."""

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import rich
from .mixins import WorkspaceLookupMixin
from .permissions import IsWorkspaceMember


class RichPreviewInputSchema(serializers.Serializer):
    profile = serializers.ChoiceField(choices=sorted(rich.PROFILES))
    source = serializers.CharField(allow_blank=True, trim_whitespace=False)


class RichPreviewSchema(serializers.Serializer):
    profile = serializers.CharField()
    length = serializers.IntegerField()
    max_length = serializers.IntegerField()
    tree = serializers.JSONField(help_text="Closed node tree; see docs/operations/RICH_CONTENT.md.")


class RichPreviewView(WorkspaceLookupMixin, APIView):
    """A signed-in workspace member sees how a piece of text will render; nothing is saved."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    @extend_schema(request=RichPreviewInputSchema, responses=RichPreviewSchema)
    def post(self, request, workspace_public_id):
        body = request.data if isinstance(request.data, dict) else {}
        name, source = body.get("profile"), body.get("source")
        if name not in rich.PROFILES:
            raise ValidationError({"profile": [f"Use one of: {', '.join(sorted(rich.PROFILES))}."]})
        if not isinstance(source, str):
            raise ValidationError({"source": ["Send the text as a string."]})
        try:
            tree = rich.render_tree(source, name)
        except rich.RichError as error:
            raise ValidationError({"source": [error.message]}) from error
        return Response(
            {
                "profile": name,
                "length": len(source),
                "max_length": rich.profile(name).max_length,
                "tree": tree,
            }
        )
