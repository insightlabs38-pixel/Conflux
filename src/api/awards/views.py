from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from evaluations.models import EvaluationPlan
from events.models import Event, Track
from events.views import OrganizerView
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Award,
    FulfillmentState,
    PrizeComponent,
    PrizeFulfillment,
    PrizePackage,
    SelectionSource,
)
from .services import advance_fulfillment, select_winner


class AwardInput(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True)
    eligibility_track = serializers.UUIDField(required=False, allow_null=True)
    require_finalized_submission = serializers.BooleanField(required=False)
    selection_source = serializers.ChoiceField(choices=SelectionSource.choices)
    evaluation_plan = serializers.UUIDField(required=False, allow_null=True)
    winner_count = serializers.IntegerField(min_value=1, max_value=100)
    allow_stacking = serializers.BooleanField(required=False)
    conflict_group = serializers.CharField(max_length=80, required=False, allow_blank=True)


class WinnerInput(serializers.Serializer):
    project = serializers.UUIDField()
    override_reason = serializers.CharField(required=False, allow_blank=True)


class CandidateOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    track = serializers.UUIDField(allow_null=True)
    has_finalized_submission = serializers.BooleanField()


class ComponentInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=PrizeComponent._meta.get_field("kind").choices)
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(min_value=1, max_value=1000)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    currency = serializers.CharField(max_length=3, required=False, allow_blank=True)


class ComponentOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    kind = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    quantity = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    currency = serializers.CharField()


class WinnerOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    project = serializers.UUIDField()
    project_name = serializers.CharField()
    source = serializers.CharField()
    evidence = serializers.JSONField()
    override_reason = serializers.CharField()
    selected_at = serializers.DateTimeField()
    fulfillments = serializers.ListField(child=serializers.DictField())


class FulfillmentInput(serializers.Serializer):
    state = serializers.ChoiceField(choices=FulfillmentState.choices)
    note = serializers.CharField(required=False, allow_blank=True)


class FulfillmentOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    component = serializers.UUIDField()
    component_name = serializers.CharField()
    state = serializers.CharField()
    note = serializers.CharField()
    updated_at = serializers.DateTimeField()


class AwardOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    eligibility_track = serializers.UUIDField(allow_null=True)
    require_finalized_submission = serializers.BooleanField()
    selection_source = serializers.CharField()
    evaluation_plan = serializers.UUIDField(allow_null=True)
    winner_count = serializers.IntegerField()
    allow_stacking = serializers.BooleanField()
    conflict_group = serializers.CharField()
    published_at = serializers.DateTimeField(allow_null=True)
    components = ComponentOutput(many=True)
    winners = WinnerOutput(many=True)


class PublicWinnerOutput(serializers.Serializer):
    project = serializers.UUIDField()
    project_name = serializers.CharField()


class PublicAwardOutput(AwardOutput):
    winners = PublicWinnerOutput(many=True)


def _winner_data(winner):
    return {
        "public_id": str(winner.public_id),
        "project": str(winner.project.public_id),
        "project_name": winner.project.name,
        "source": winner.source,
        "evidence": winner.evidence,
        "override_reason": winner.override_reason,
        "selected_at": winner.selected_at,
        "fulfillments": [
            _fulfillment_data(item) for item in winner.fulfillments.select_related("component")
        ],
    }


def _fulfillment_data(item):
    return {
        "public_id": str(item.public_id),
        "component": str(item.component.public_id),
        "component_name": item.component.name,
        "state": item.state,
        "note": item.note,
        "updated_at": item.updated_at,
    }


def _component_data(component):
    return {
        "public_id": str(component.public_id),
        "kind": component.kind,
        "name": component.name,
        "description": component.description,
        "quantity": component.quantity,
        "amount": component.amount,
        "currency": component.currency,
    }


def _award_data(award):
    package = PrizePackage.objects.filter(award=award).first()
    return {
        "public_id": str(award.public_id),
        "name": award.name,
        "description": award.description,
        "eligibility_track": str(award.eligibility_track.public_id)
        if award.eligibility_track
        else None,
        "require_finalized_submission": award.require_finalized_submission,
        "selection_source": award.selection_source,
        "evaluation_plan": str(award.evaluation_plan.public_id) if award.evaluation_plan else None,
        "winner_count": award.winner_count,
        "allow_stacking": award.allow_stacking,
        "conflict_group": award.conflict_group,
        "published_at": award.published_at,
        "components": [_component_data(item) for item in package.components.all()]
        if package
        else [],
        "winners": [_winner_data(item) for item in award.winners.select_related("project")],
    }


class AwardBase(OrganizerView):
    def get_award(self, award_public_id):
        return get_object_or_404(Award, event=self.get_event(), public_id=award_public_id)


class AwardListView(AwardBase):
    @extend_schema(responses=AwardOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            [
                _award_data(item)
                for item in Award.objects.filter(event=self.get_event()).order_by("pk")
            ]
        )

    @extend_schema(request=AwardInput, responses={201: AwardOutput})
    def post(self, request, workspace_public_id, event_public_id):
        data = AwardInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data.copy()
        event = self.get_event()
        self.ensure_mutable(event)
        track_id = values.pop("eligibility_track", None)
        plan_id = values.pop("evaluation_plan", None)
        if track_id:
            values["eligibility_track"] = get_object_or_404(Track, event=event, public_id=track_id)
        if plan_id:
            values["evaluation_plan"] = get_object_or_404(
                EvaluationPlan, stage__event=event, public_id=plan_id
            )
        try:
            with transaction.atomic():
                award = Award(event=event, **values)
                award.full_clean()
                award.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="award.created",
                    target=award,
                    event_type="award.created",
                    payload={"event": str(event.public_id), "award": str(award.public_id)},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_award_data(award), status=201)


class AwardCandidateView(AwardBase):
    @extend_schema(responses=CandidateOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        projects = (
            Project.objects.filter(event=self.get_event())
            .select_related("track")
            .order_by("name", "pk")
        )
        return Response(
            [
                {
                    "public_id": str(project.public_id),
                    "name": project.name,
                    "track": str(project.track.public_id) if project.track else None,
                    "has_finalized_submission": project.submissions.filter(
                        status="finalized"
                    ).exists(),
                }
                for project in projects
            ]
        )


class AwardWinnerView(AwardBase):
    @extend_schema(request=WinnerInput, responses={201: WinnerOutput})
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        data = WinnerInput(data=request.data)
        data.is_valid(raise_exception=True)
        award = self.get_award(award_public_id)
        self.ensure_mutable(award.event)
        project = get_object_or_404(
            Project, event=award.event, public_id=data.validated_data["project"]
        )
        try:
            winner = select_winner(
                award=award,
                project=project,
                actor=request.user,
                override_reason=data.validated_data.get("override_reason", ""),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_winner_data(winner), status=201)


class AwardPublishView(AwardBase):
    @extend_schema(request=None, responses=AwardOutput)
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        self.ensure_mutable(self.get_event())
        with transaction.atomic():
            award = get_object_or_404(
                Award.objects.select_for_update(), event=self.get_event(), public_id=award_public_id
            )
            if award.published_at:
                raise ValidationError("Award is already published.")
            if award.winners.count() != award.winner_count:
                raise ValidationError("Fill all winner positions before publication.")
            award.published_at = timezone.now()
            award.save(update_fields=["published_at"])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="award.published",
                target=award,
                event_type="award.published",
                payload={"event": str(award.event.public_id), "award": str(award.public_id)},
            )
        return Response(_award_data(award))


class AwardComponentView(AwardBase):
    @extend_schema(request=ComponentInput, responses={201: ComponentOutput})
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        data = ComponentInput(data=request.data)
        data.is_valid(raise_exception=True)
        award = self.get_award(award_public_id)
        self.ensure_mutable(award.event)
        try:
            with transaction.atomic():
                award = Award.objects.select_for_update().get(pk=award.pk)
                if award.published_at:
                    raise ValidationError("Published awards cannot be changed.")
                package, _ = PrizePackage.objects.get_or_create(
                    award=award, defaults={"name": award.name}
                )
                component = PrizeComponent(package=package, **data.validated_data)
                component.full_clean()
                component.save()
                PrizeFulfillment.objects.bulk_create(
                    [
                        PrizeFulfillment(winner=winner, component=component)
                        for winner in award.winners.all()
                    ]
                )
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="prize.component_added",
                    target=component,
                    event_type="prize.component_added",
                    payload={"event": str(award.event.public_id), "award": str(award.public_id)},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_component_data(component), status=201)


class FulfillmentView(AwardBase):
    @extend_schema(request=FulfillmentInput, responses=FulfillmentOutput)
    def patch(
        self, request, workspace_public_id, event_public_id, award_public_id, fulfillment_public_id
    ):
        data = FulfillmentInput(data=request.data)
        data.is_valid(raise_exception=True)
        fulfillment = get_object_or_404(
            PrizeFulfillment,
            public_id=fulfillment_public_id,
            winner__award=self.get_award(award_public_id),
        )
        try:
            updated = advance_fulfillment(
                fulfillment=fulfillment,
                target=data.validated_data["state"],
                actor=request.user,
                note=data.validated_data.get("note", ""),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_fulfillment_data(updated))


class PublicAwardsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=PublicAwardOutput(many=True))
    def get(self, request, event_public_id):
        event = get_object_or_404(Event, public_id=event_public_id, is_public=True)
        awards = []
        for award in Award.objects.filter(event=event, published_at__isnull=False).order_by("pk"):
            row = _award_data(award)
            row["winners"] = [
                {"project": winner["project"], "project_name": winner["project_name"]}
                for winner in row["winners"]
            ]
            awards.append(row)
        return Response(awards)
