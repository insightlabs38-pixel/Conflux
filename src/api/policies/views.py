from audit.services import diff_snapshots, record_mutation, snapshot_fields
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from participation.models import Team
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .debugger import debug_action
from .evaluator import PolicyError
from .models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from .presets import PRESETS, build_preset_ast
from .serializers import (
    ExceptionGrantSerializer,
    PolicyBindingSerializer,
    PolicySerializer,
    TemporalGateSerializer,
    TimelineWindowSchema,
)
from .timezone_safety import dst_warning, local_iso


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class PolicyDebugInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=Action.choices)
    subject_type = serializers.ChoiceField(choices=["project", "team"], required=False)
    subject_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if ("subject_type" in attrs) != ("subject_id" in attrs):
            raise serializers.ValidationError("Supply subject_type and subject_id together.")
        expected = {Action.SUBMIT: "project", Action.JOIN: "team"}.get(attrs["action"])
        if "subject_type" in attrs and attrs["subject_type"] != expected:
            raise serializers.ValidationError("This action does not use that subject type.")
        return attrs


class PolicyDebugResponse(serializers.Serializer):
    action = serializers.ChoiceField(choices=Action.choices)
    subject_type = serializers.CharField(allow_null=True)
    subject_id = serializers.UUIDField(allow_null=True)
    checked_at = serializers.DateTimeField()
    facts = serializers.JSONField()
    policy = serializers.JSONField(allow_null=True)
    policy_allowed = serializers.BooleanField(allow_null=True)
    allowed = serializers.BooleanField()
    reason = serializers.CharField()
    exception_grant_reason = serializers.CharField(allow_null=True)
    error = serializers.CharField(allow_null=True)
    trace = serializers.JSONField(allow_null=True)


class PolicyDebugView(OrganizerView):
    @extend_schema(request=PolicyDebugInput, responses=PolicyDebugResponse)
    def post(self, request, workspace_public_id, event_public_id):
        serializer = PolicyDebugInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        event = self.get_event()
        subject_type = data.get("subject_type")
        subject_id = data.get("subject_id")
        if subject_id is not None:
            model = Project if subject_type == "project" else Team
            get_object_or_404(model, event=event, public_id=subject_id)
        return Response(
            debug_action(
                event,
                data["action"],
                subject_type=subject_type,
                subject_id=str(subject_id) if subject_id else None,
            )
        )


class PresetListView(OrganizerView):
    @extend_schema(
        responses={
            200: {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "params": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["label", "params"],
                },
            }
        }
    )
    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            {slug: {"label": p["label"], "params": p["params"]} for slug, p in PRESETS.items()}
        )


class PolicyListView(OrganizerView):
    serializer_class = PolicySerializer

    def get(self, request, workspace_public_id, event_public_id):
        return Response(PolicySerializer(self.get_event().policies.all(), many=True).data)

    @extend_schema(responses={201: PolicySerializer})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        serializer = PolicySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ast = data.get("ast")
        if not ast:
            try:
                ast = build_preset_ast(data["preset"], data.get("preset_params"))
            except PolicyError as exc:
                raise ValidationError({"preset": str(exc)}) from exc
        try:
            with transaction.atomic():
                policy = Policy(event=event, name=data["name"], ast=ast)
                policy.full_clean()
                policy.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="policy.created",
                    target=policy,
                    event_type="policy.created",
                    payload={"event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "A policy with this name already exists."}) from exc
        return Response(PolicySerializer(policy).data, status=201)


class PolicyDetailView(OrganizerView):
    @extend_schema(request=PolicySerializer, responses=PolicySerializer)
    @transaction.atomic
    def patch(self, request, workspace_public_id, event_public_id, policy_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        policy = get_object_or_404(
            Policy.objects.select_for_update(), event=event, public_id=policy_public_id
        )
        serializer = PolicySerializer(policy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "preset" in data:
            try:
                data["ast"] = build_preset_ast(data.pop("preset"), data.pop("preset_params", None))
            except PolicyError as exc:
                raise ValidationError({"preset": str(exc)}) from exc
        fields = [field for field in ("name", "ast") if field in data]
        before = snapshot_fields(policy, fields)
        try:
            with transaction.atomic():
                for field in fields:
                    setattr(policy, field, data[field])
                policy.full_clean()
                policy.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="policy.updated",
                    target=policy,
                    event_type="policy.updated",
                    payload={"event": str(event.public_id)},
                    metadata={
                        "event_id": str(event.public_id),
                        "changes": diff_snapshots(before, snapshot_fields(policy, fields)),
                    },
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(PolicySerializer(policy).data)

    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, policy_public_id):
        policy = get_object_or_404(Policy, event=self.get_event(), public_id=policy_public_id)
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="policy.deleted",
                target=policy,
                event_type="policy.deleted",
                payload={"event": str(policy.event.public_id)},
            )
            policy.delete()
        return Response(status=204)


class PolicyBindingListView(OrganizerView):
    serializer_class = PolicyBindingSerializer

    def get(self, request, workspace_public_id, event_public_id):
        bindings = PolicyBinding.objects.filter(event=self.get_event())
        return Response(PolicyBindingSerializer(bindings, many=True).data)

    @extend_schema(responses={201: PolicyBindingSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        serializer = PolicyBindingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        policy = get_object_or_404(
            Policy, event=event, public_id=serializer.validated_data["policy"]
        )
        try:
            with transaction.atomic():
                binding = PolicyBinding(
                    event=event, action=serializer.validated_data["action"], policy=policy
                )
                binding.full_clean()
                binding.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="policy_binding.created",
                    target=binding,
                    event_type="policy_binding.created",
                    payload={"event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "This action already has a policy bound."}) from exc
        return Response(PolicyBindingSerializer(binding).data, status=201)


class PolicyBindingDetailView(OrganizerView):
    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, binding_public_id):
        binding = get_object_or_404(
            PolicyBinding, event=self.get_event(), public_id=binding_public_id
        )
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="policy_binding.deleted",
                target=binding,
                event_type="policy_binding.deleted",
                payload={"event": str(self.get_event().public_id)},
            )
            binding.delete()
        return Response(status=204)


class TemporalGateListView(OrganizerView):
    serializer_class = TemporalGateSerializer

    def get(self, request, workspace_public_id, event_public_id):
        gates = self.get_event().temporal_gates.select_related("event").all()
        return Response(TemporalGateSerializer(gates, many=True).data)

    @extend_schema(responses={201: TemporalGateSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        serializer = TemporalGateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                gate = TemporalGate(event=event, **serializer.validated_data)
                gate.full_clean()
                gate.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="temporal_gate.created",
                    target=gate,
                    event_type="temporal_gate.created",
                    payload={"event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "A gate with this name already exists."}) from exc
        return Response(TemporalGateSerializer(gate).data, status=201)


class TemporalGateDetailView(OrganizerView):
    serializer_class = TemporalGateSerializer

    def get_gate(self, gate_public_id):
        return get_object_or_404(TemporalGate, event=self.get_event(), public_id=gate_public_id)

    def patch(self, request, workspace_public_id, event_public_id, gate_public_id):
        gate = self.get_gate(gate_public_id)
        serializer = TemporalGateSerializer(gate, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed_fields = list(serializer.validated_data.keys())
        before = snapshot_fields(gate, changed_fields)
        try:
            with transaction.atomic():
                for field, value in serializer.validated_data.items():
                    setattr(gate, field, value)
                gate.full_clean()
                gate.save()
                changes = diff_snapshots(before, snapshot_fields(gate, changed_fields))
                metadata = {"event_id": str(gate.event.public_id)}
                if changes:
                    metadata["changes"] = changes
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="temporal_gate.updated",
                    target=gate,
                    event_type="temporal_gate.updated",
                    payload={"event": str(gate.event.public_id)},
                    metadata=metadata,
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(TemporalGateSerializer(gate).data)


class TimezoneTimelineView(OrganizerView):
    """The event's own start/end plus every `TemporalGate`, sorted by their
    authoritative UTC instant, each annotated with its event-local
    rendering and DST warning (VS24) -- one place an organizer can see
    everything time-boxed about the event without cross-referencing gates
    and event settings separately.
    """

    serializer_class = TimelineWindowSchema

    @extend_schema(responses=TimelineWindowSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        windows = [
            {"label": "Event window", "opens_at": event.starts_at, "closes_at": event.ends_at}
        ]
        windows += [
            {"label": gate.name, "opens_at": gate.opens_at, "closes_at": gate.closes_at}
            for gate in event.temporal_gates.order_by("name")
        ]
        windows.sort(key=lambda w: (w["opens_at"] is None, w["opens_at"]))
        return Response(
            [
                {
                    **window,
                    "event_local_opens_at": local_iso(window["opens_at"], event.timezone),
                    "event_local_closes_at": local_iso(window["closes_at"], event.timezone),
                    "dst_warning": dst_warning(
                        window["opens_at"], window["closes_at"], event.timezone
                    ),
                }
                for window in windows
            ]
        )

    def delete(self, request, workspace_public_id, event_public_id, gate_public_id):
        gate = self.get_gate(gate_public_id)
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="temporal_gate.deleted",
                target=gate,
                event_type="temporal_gate.deleted",
                payload={"event": str(gate.event.public_id)},
            )
            gate.delete()
        return Response(status=204)


class ExceptionGrantListView(OrganizerView):
    serializer_class = ExceptionGrantSerializer

    def get(self, request, workspace_public_id, event_public_id):
        grants = ExceptionGrant.objects.filter(event=self.get_event())
        return Response(ExceptionGrantSerializer(grants, many=True).data)

    @extend_schema(responses={201: ExceptionGrantSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        serializer = ExceptionGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            grant = ExceptionGrant.objects.create(
                event=event, granted_by=request.user, **serializer.validated_data
            )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="exception_grant.created",
                target=grant,
                event_type="exception_grant.created",
                payload={"event": str(event.public_id)},
            )
        return Response(ExceptionGrantSerializer(grant).data, status=201)
