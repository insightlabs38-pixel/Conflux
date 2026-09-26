from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .evaluator import PolicyError
from .models import ExceptionGrant, Policy, PolicyBinding, TemporalGate
from .presets import PRESETS, build_preset_ast
from .serializers import (
    ExceptionGrantSerializer,
    PolicyBindingSerializer,
    PolicySerializer,
    TemporalGateSerializer,
)


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class PresetListView(OrganizerView):
    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            {slug: {"label": p["label"], "params": p["params"]} for slug, p in PRESETS.items()}
        )


class PolicyListView(OrganizerView):
    def get(self, request, workspace_public_id, event_public_id):
        return Response(PolicySerializer(self.get_event().policies.all(), many=True).data)

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
    def get(self, request, workspace_public_id, event_public_id):
        bindings = PolicyBinding.objects.filter(event=self.get_event())
        return Response(PolicyBindingSerializer(bindings, many=True).data)

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
    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            TemporalGateSerializer(self.get_event().temporal_gates.all(), many=True).data
        )

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
    def get_gate(self, gate_public_id):
        return get_object_or_404(TemporalGate, event=self.get_event(), public_id=gate_public_id)

    def patch(self, request, workspace_public_id, event_public_id, gate_public_id):
        gate = self.get_gate(gate_public_id)
        serializer = TemporalGateSerializer(gate, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                for field, value in serializer.validated_data.items():
                    setattr(gate, field, value)
                gate.full_clean()
                gate.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="temporal_gate.updated",
                    target=gate,
                    event_type="temporal_gate.updated",
                    payload={"event": str(gate.event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(TemporalGateSerializer(gate).data)

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
    def get(self, request, workspace_public_id, event_public_id):
        grants = ExceptionGrant.objects.filter(event=self.get_event())
        return Response(ExceptionGrantSerializer(grants, many=True).data)

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
