"""The read-only completeness report (PD-F003-B01-T01): which feature provides what, checked."""

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from . import features
from .mixins import WorkspaceLookupMixin
from .permissions import require_roles


class CompletenessPropertySchema(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    batch = serializers.CharField()
    landed = serializers.BooleanField()


class CompletenessClaimSchema(serializers.Serializer):
    state = serializers.ChoiceField(choices=list(features.STATES))
    refs = serializers.ListField(child=serializers.CharField())
    reason = serializers.CharField(allow_blank=True)
    owner = serializers.CharField(allow_blank=True)


class CompletenessStateSchema(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class CompletenessLifecycleSchema(serializers.Serializer):
    kind = serializers.CharField()
    field = serializers.CharField(allow_blank=True)
    initial = serializers.ListField(child=serializers.CharField())
    terminal = serializers.ListField(child=serializers.CharField())
    via = serializers.ListField(child=serializers.CharField())
    note = serializers.CharField(allow_blank=True)
    transitions = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))


class CompletenessProblemSchema(serializers.Serializer):
    code = serializers.CharField()
    feature = serializers.CharField(allow_null=True)
    property = serializers.CharField(allow_null=True)
    message = serializers.CharField()


class CompletenessFeatureSchema(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    model = serializers.CharField()
    id_field = serializers.CharField()
    id_type = serializers.CharField(allow_null=True)
    states = CompletenessStateSchema(many=True)
    lifecycle = CompletenessLifecycleSchema(allow_null=True)
    claims = serializers.DictField(child=CompletenessClaimSchema())
    problems = CompletenessProblemSchema(many=True)


class CompletenessSchema(serializers.Serializer):
    properties = CompletenessPropertySchema(many=True)
    features = CompletenessFeatureSchema(many=True)
    totals = serializers.DictField(child=serializers.DictField(child=serializers.IntegerField()))
    problems = CompletenessProblemSchema(many=True)
    ok = serializers.BooleanField()


class CompletenessView(WorkspaceLookupMixin, APIView):
    """Organizers and admins read it; nothing about it can be written or changes a request."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=CompletenessSchema)
    def get(self, request, workspace_public_id):
        response = Response(features.report())
        response["Cache-Control"] = "private, no-store"
        return response
