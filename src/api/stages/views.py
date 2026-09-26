from audit.models import AuditEvent
from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .advancement import REGISTRY, Candidate, advance_stage
from .graph import StageGraphError, topological_order, validate_event_graph
from .models import Stage, StageTransition
from .serializers import StageSerializer, StageTransitionSerializer


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class StageEventMixin(OrganizerView):
    def get_stage(self):
        return get_object_or_404(
            Stage, event=self.get_event(), public_id=self.kwargs["stage_public_id"]
        )


class StageListView(StageEventMixin):
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        try:
            ordered = topological_order(event)
        except StageGraphError:
            # A cycle can only exist here via a bulk write that bypassed
            # StageTransition.clean() (see ST-002) — fall back to a stable
            # order rather than 500ing the organizer's own stage list.
            ordered = list(event.stages.all())
        return Response(StageSerializer(ordered, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        serializer = StageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                stage = Stage(event=event, **serializer.validated_data)
                stage.full_clean()
                stage.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="stage.created",
                    target=stage,
                    event_type="stage.created",
                    payload={"event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "A stage with this name already exists in this event."}
            ) from exc
        return Response(StageSerializer(stage).data, status=201)


class StageDetailView(StageEventMixin):
    def patch(self, request, workspace_public_id, event_public_id, stage_public_id):
        stage = self.get_stage()
        serializer = StageSerializer(stage, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                for field, value in serializer.validated_data.items():
                    setattr(stage, field, value)
                stage.full_clean()
                stage.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="stage.updated",
                    target=stage,
                    event_type="stage.updated",
                    payload={"event": str(stage.event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "A stage with this name already exists in this event."}
            ) from exc
        return Response(StageSerializer(stage).data)

    def delete(self, request, workspace_public_id, event_public_id, stage_public_id):
        stage = self.get_stage()
        if stage.entries.exists():
            raise ValidationError(
                {"detail": "A stage that has ever held a participant cannot be deleted."}
            )
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="stage.deleted",
                target=stage,
                event_type="stage.deleted",
                payload={"event": str(stage.event.public_id)},
            )
            stage.delete()
        return Response(status=204)


class StageTransitionListView(StageEventMixin):
    def get(self, request, workspace_public_id, event_public_id):
        transitions = StageTransition.objects.filter(from_stage__event=self.get_event())
        return Response(StageTransitionSerializer(transitions, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        serializer = StageTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from_stage = get_object_or_404(
            Stage, event=event, public_id=serializer.validated_data["from_stage"]
        )
        to_stage = get_object_or_404(
            Stage, event=event, public_id=serializer.validated_data["to_stage"]
        )
        try:
            with transaction.atomic():
                transition = StageTransition(from_stage=from_stage, to_stage=to_stage)
                transition.full_clean()
                transition.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="stage_transition.created",
                    target=transition,
                    event_type="stage_transition.created",
                    payload={"event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "This transition already exists."}) from exc
        return Response(StageTransitionSerializer(transition).data, status=201)


class StageTransitionDetailView(StageEventMixin):
    def delete(self, request, workspace_public_id, event_public_id, transition_public_id):
        transition = get_object_or_404(
            StageTransition, from_stage__event=self.get_event(), public_id=transition_public_id
        )
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="stage_transition.deleted",
                target=transition,
                event_type="stage_transition.deleted",
                payload={"event": str(self.get_event().public_id)},
            )
            transition.delete()
        return Response(status=204)


class GraphValidationView(StageEventMixin):
    """GET: the current stage graph's validity and, if valid, its
    deterministic display order — what the builder UI polls to show a
    live "this graph is broken" indicator without guessing at the rules
    client-side.
    """

    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        try:
            validate_event_graph(event)
        except StageGraphError as exc:
            errors = exc.messages if hasattr(exc, "messages") else [str(exc)]
            return Response({"valid": False, "errors": errors})
        ordered = topological_order(event)
        return Response({"valid": True, "order": [str(s.public_id) for s in ordered]})


class StageAdvancementView(StageEventMixin):
    """POST: run an AdvancementStrategy from this stage to `to_stage`.
    Candidates are supplied explicitly by the caller (real per-project
    scoring is a later batch); the result and its evidence trail come back
    from `advance_stage` itself.
    """

    def get(self, request, workspace_public_id, event_public_id, stage_public_id):
        return Response({"strategies": sorted(REGISTRY)})

    def post(self, request, workspace_public_id, event_public_id, stage_public_id):
        stage = self.get_stage()
        to_stage = get_object_or_404(
            Stage, event=stage.event, public_id=request.data.get("to_stage")
        )
        strategy_slug = request.data.get("strategy", "")
        params = request.data.get("params") or {}
        candidates = [
            Candidate(
                subject_type=c["subject_type"],
                subject_id=c["subject_id"],
                score=c.get("score"),
                track_id=c.get("track_id"),
            )
            for c in request.data.get("candidates", [])
        ]
        try:
            advanced = advance_stage(
                stage, to_stage, strategy_slug, candidates, actor=request.user, params=params
            )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response({"advanced": advanced})


class StageEvidenceView(StageEventMixin):
    """GET: the most recent audited advancement decisions for this event —
    the organizer-facing evidence trail for "why did this happen".
    """

    def get(self, request, workspace_public_id, event_public_id):
        rows = AuditEvent.objects.filter(
            workspace=self.get_workspace(), action="stage.advanced"
        ).order_by("-created_at")[:20]
        return Response(
            [
                {
                    "created_at": row.created_at,
                    "actor": row.actor.username if row.actor else None,
                    "stage_public_id": row.target_id,
                    "metadata": row.metadata,
                }
                for row in rows
            ]
        )
