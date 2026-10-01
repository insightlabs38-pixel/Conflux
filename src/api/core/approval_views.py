"""Approval endpoints (PD-F002-B01-T06): the queue, a decision, a withdrawal, and the gates.

Who sees a request: the person who asked and anyone holding a deciding role of its policy. Anyone
else gets 404, never 403. Gates are switched by organizers and admins.
"""

from accounts.authentication import CookieSessionAuthentication
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event, EventStatus
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from . import approvals
from .authz import has_any_role
from .mixins import WorkspaceLookupMixin
from .models import ApprovalDecision, ApprovalRequest
from .pagination import page_params, paged_response
from .permissions import IsWorkspaceMember, require_roles


class ApprovalSubjectSchema(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.CharField()


class ApprovalDecisionSchema(serializers.Serializer):
    actor = serializers.CharField()
    decision = serializers.ChoiceField(choices=ApprovalDecision.Decision.choices)
    note = serializers.CharField()
    at = serializers.DateTimeField()


class ApprovalSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    action = serializers.CharField()
    label = serializers.CharField()
    subject = ApprovalSubjectSchema(allow_null=True)
    summary = serializers.ListField(child=serializers.CharField())
    status = serializers.ChoiceField(choices=ApprovalRequest.Status.choices)
    requested_by = serializers.CharField()
    required_approvals = serializers.IntegerField()
    approvals = serializers.IntegerField()
    decisions = ApprovalDecisionSchema(many=True)
    expires_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    executed_at = serializers.DateTimeField(allow_null=True)
    can_decide = serializers.BooleanField()
    can_cancel = serializers.BooleanField()


class ApprovalDecisionInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ApprovalDecision.Decision.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=approvals.MAX_NOTE)


class GateSchema(serializers.Serializer):
    action = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    deciders = serializers.ListField(child=serializers.CharField())
    min_approvals = serializers.IntegerField()
    enabled = serializers.BooleanField()


class GateInput(serializers.Serializer):
    enabled = serializers.BooleanField()


class _EventView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    def deciding_actions(self):
        return [
            key
            for key, policy in approvals.POLICIES.items()
            if has_any_role(self.request.user, self.get_workspace(), *policy.deciders)
        ]

    def visible(self):
        found = ApprovalRequest.objects.filter(event=self.get_event()).select_related(
            "workspace", "requested_by"
        )
        return found.filter(
            Q(requested_by=self.request.user) | Q(action__in=self.deciding_actions())
        )

    def get_request(self):
        return get_object_or_404(self.visible(), public_id=self.kwargs["approval_public_id"])


class ApprovalListView(_EventView):
    @extend_schema(
        parameters=[
            OpenApiParameter("status", str, enum=ApprovalRequest.Status.values),
            OpenApiParameter("action", str),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=ApprovalSchema(many=True),
    )
    def get(self, request, workspace_public_id, event_public_id):
        limit, offset = page_params(request, default=25, maximum=100)
        found = self.visible()
        wanted = request.query_params.get("status")
        if wanted and wanted not in ApprovalRequest.Status.values:
            allowed = ", ".join(ApprovalRequest.Status.values)
            raise ValidationError({"status": [f"Use one of {allowed}."]})
        action = request.query_params.get("action")
        if action:
            found = found.filter(action=action)
        now = timezone.now()
        lapsed = Q(status__in=("pending", "approved"), expires_at__lte=now)
        if wanted == "expired":  # past its expiry counts as expired before the sweep marks it
            found = found.filter(Q(status="expired") | lapsed)
        elif wanted:
            found = found.filter(status=wanted).exclude(lapsed)
        return paged_response(
            request,
            found.prefetch_related("decisions__actor"),
            lambda page: [approvals.describe(item, request.user) for item in page],
            limit=limit,
            offset=offset,
        )


class ApprovalDetailView(_EventView):
    @extend_schema(responses=ApprovalSchema)
    def get(self, request, workspace_public_id, event_public_id, approval_public_id):
        return Response(approvals.describe(self.get_request(), request.user))


class ApprovalDecisionView(_EventView):
    @extend_schema(request=ApprovalDecisionInput, responses=ApprovalSchema)
    def post(self, request, workspace_public_id, event_public_id, approval_public_id):
        item = self.get_request()
        data = ApprovalDecisionInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            approvals.decide(
                item,
                request.user,
                data.validated_data["decision"],
                data.validated_data.get("note", ""),
            )
        except approvals.ApprovalStateError as exc:
            return Response({"code": "approval_closed", "detail": str(exc)}, status=409)
        return Response(approvals.describe(self.get_request(), request.user))


class ApprovalCancelView(_EventView):
    @extend_schema(request=None, responses=ApprovalSchema)
    def post(self, request, workspace_public_id, event_public_id, approval_public_id):
        item = self.get_request()
        try:
            approvals.cancel(item, request.user)
        except approvals.ApprovalStateError as exc:
            return Response({"code": "approval_closed", "detail": str(exc)}, status=409)
        return Response(approvals.describe(self.get_request(), request.user))


def _gates(event):
    enabled = set(event.approval_gates.filter(enabled=True).values_list("action", flat=True))
    return [
        {
            "action": policy.key,
            "label": policy.label,
            "description": policy.description,
            "deciders": list(policy.deciders),
            "min_approvals": policy.min_approvals,
            "enabled": policy.key in enabled,
        }
        for policy in approvals.POLICIES.values()
    ]


class ApprovalGateListView(_EventView):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=GateSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response(_gates(self.get_event()))


class ApprovalGateView(_EventView):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(request=GateInput, responses=GateSchema)
    def put(self, request, workspace_public_id, event_public_id, action):
        event = self.get_event()
        if event.status == EventStatus.ARCHIVED:
            raise ValidationError({"status": "Archived event configuration cannot be edited."})
        data = GateInput(data=request.data)
        data.is_valid(raise_exception=True)
        approvals.set_gate(
            event=event, actor=request.user, action=action, enabled=data.validated_data["enabled"]
        )
        return Response(next(g for g in _gates(event) if g["action"] == action))
