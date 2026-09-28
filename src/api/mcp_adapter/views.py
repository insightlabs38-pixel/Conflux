import json

from accounts.authentication import CookieSessionAuthentication
from accounts.models import ApiCredential
from audit.services import record_mutation
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Event
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import server

MAX_BODY_BYTES = 256 * 1024


class JsonRpcMessage(serializers.Serializer):
    jsonrpc = serializers.CharField()
    id = serializers.JSONField(required=False)
    method = serializers.CharField()
    params = serializers.DictField(required=False)


class McpEndpointView(APIView):
    """Streamable-HTTP MCP endpoint (POST only, JSON responses, no server push).

    Callable only with an API credential that allows `POST:mcp-endpoint`; a browser
    session cookie is refused so a web page can never drive it.
    """

    http_method_names = ["post", "options"]
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        origin = request.META.get("HTTP_ORIGIN")
        if origin and origin not in settings.CSRF_TRUSTED_ORIGINS:
            from urllib.parse import urlsplit

            if urlsplit(origin).netloc != request.get_host():
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Origin not allowed.")
        super().initial(request, *args, **kwargs)

    @extend_schema(request=JsonRpcMessage, responses={200: JsonRpcMessage, 202: None})
    def post(self, request, workspace_public_id, event_public_id):
        credential = request.auth
        if not isinstance(credential, ApiCredential):
            return Response({"detail": "MCP requires an API credential."}, status=403)
        event = get_object_or_404(
            Event, public_id=event_public_id, workspace__public_id=workspace_public_id
        )
        raw = request.body
        if len(raw) > MAX_BODY_BYTES:
            return Response(server.error(None, -32600, "Request too large."), status=413)
        try:
            message = json.loads(raw)
        except ValueError:
            return Response(server.error(None, -32700, "Parse error."))
        if isinstance(message, list):
            return Response(server.error(None, -32600, "Batching is not supported."))

        def audit(tool, status, argument_names):
            with transaction.atomic():
                record_mutation(
                    actor=credential.owner,
                    workspace=event.workspace,
                    action="mcp.tool_called",
                    target=credential,
                    metadata={
                        "tool": tool.name,
                        "status": status,
                        "arguments": argument_names,
                        "event": str(event.public_id),
                    },
                )

        reply = server.handle(
            message,
            credential,
            request._request,
            {"workspace_public_id": workspace_public_id, "event_public_id": event_public_id},
            audit,
        )
        return Response(status=202) if reply is None else Response(reply)
