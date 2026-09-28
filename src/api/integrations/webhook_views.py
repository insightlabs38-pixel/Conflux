import hashlib
import re

from accounts.authentication import CookieOnlyAuthentication
from audit.services import record_mutation
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .models import WebhookDelivery, WebhookPlatform, WebhookSubscription
from .webhooks import delivery_body, signing_secret, validate_destination

EVENT_TYPE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


class SubscriptionInput(serializers.Serializer):
    url = serializers.URLField(max_length=2048)
    event_types = serializers.ListField(child=serializers.CharField(), min_length=1, max_length=50)
    event = serializers.UUIDField(required=False, allow_null=True)
    platform = serializers.ChoiceField(choices=WebhookPlatform.choices, required=False)


class SubscriptionOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    url = serializers.URLField()
    event_types = serializers.ListField(child=serializers.CharField())
    event = serializers.UUIDField(allow_null=True)
    platform = serializers.CharField()
    enabled = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class SubscriptionIssued(SubscriptionOutput):
    secret = serializers.CharField()


class SubscriptionUpdate(serializers.Serializer):
    enabled = serializers.BooleanField(required=False)
    url = serializers.URLField(max_length=2048, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide enabled or url.")
        if "url" in attrs:
            try:
                validate_destination(attrs["url"])
            except ValueError as exc:
                raise serializers.ValidationError({"url": str(exc)}) from exc
        return attrs


class DeliveryOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    event_id = serializers.UUIDField()
    event_type = serializers.CharField()
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    last_status_code = serializers.IntegerField(allow_null=True)
    last_error = serializers.CharField()
    next_attempt_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)


class AttemptOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    destination = serializers.URLField()
    body = serializers.CharField()
    headers = serializers.DictField(child=serializers.CharField())
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)
    status_code = serializers.IntegerField(allow_null=True)
    error = serializers.CharField()


class DeliveryInspection(DeliveryOutput):
    destination = serializers.URLField()
    next_body = serializers.CharField()
    body_sha256 = serializers.CharField()
    signature_scheme = serializers.CharField()
    history = AttemptOutput(many=True)
    history_has_more = serializers.BooleanField()


def history_offset(request):
    try:
        offset = int(request.query_params.get("offset", "0"))
    except ValueError as exc:
        raise ValidationError({"offset": "Must be a nonnegative integer."}) from exc
    if offset < 0:
        raise ValidationError({"offset": "Must be a nonnegative integer."})
    return offset


def subscription_data(item):
    return {
        "public_id": str(item.public_id),
        "url": item.url,
        "event_types": item.event_types,
        "event": str(item.event.public_id) if item.event else None,
        "platform": item.platform,
        "enabled": item.enabled,
        "created_at": item.created_at,
    }


def delivery_data(item):
    return {
        "public_id": str(item.public_id),
        "event_id": str(item.domain_event.public_id),
        "event_type": item.domain_event.event_type,
        "status": item.status,
        "attempts": item.attempts,
        "last_status_code": item.last_status_code,
        "last_error": item.last_error,
        "next_attempt_at": item.next_attempt_at,
        "created_at": item.created_at,
        "completed_at": item.completed_at,
    }


class WebhookBase(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieOnlyAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get_subscription(self, subscription_public_id):
        return get_object_or_404(
            WebhookSubscription.objects.select_related("event"),
            public_id=subscription_public_id,
            workspace=self.get_workspace(),
        )


class WebhookSubscriptionsView(WebhookBase):
    @extend_schema(responses=SubscriptionOutput(many=True))
    def get(self, request, workspace_public_id):
        items = (
            WebhookSubscription.objects.filter(workspace=self.get_workspace())
            .select_related("event")
            .order_by("-created_at")
        )
        return Response([subscription_data(item) for item in items])

    @extend_schema(request=SubscriptionInput, responses={201: SubscriptionIssued})
    def post(self, request, workspace_public_id):
        data = SubscriptionInput(data=request.data)
        data.is_valid(raise_exception=True)
        url = data.validated_data["url"]
        try:
            validate_destination(url)
        except ValueError as exc:
            raise ValidationError({"url": str(exc)}) from exc
        event_types = data.validated_data["event_types"]
        if len(event_types) != len(set(event_types)) or any(
            not EVENT_TYPE.fullmatch(value) for value in event_types
        ):
            raise ValidationError({"event_types": "Enter unique dotted event types."})
        event_id = data.validated_data.get("event")
        event = (
            get_object_or_404(Event, public_id=event_id, workspace=self.get_workspace())
            if event_id
            else None
        )
        with transaction.atomic():
            item = WebhookSubscription.objects.create(
                workspace=self.get_workspace(),
                event=event,
                url=url,
                event_types=event_types,
                platform=data.validated_data.get("platform", WebhookPlatform.GENERIC),
            )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="webhook.created",
                target=item,
            )
        return Response({**subscription_data(item), "secret": signing_secret(item)}, status=201)


class WebhookSubscriptionView(WebhookBase):
    @extend_schema(request=SubscriptionUpdate, responses=SubscriptionOutput)
    def patch(self, request, workspace_public_id, subscription_public_id):
        data = SubscriptionUpdate(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            item = self.get_subscription(subscription_public_id)
            for field, value in data.validated_data.items():
                setattr(item, field, value)
            item.save(update_fields=list(data.validated_data))
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="webhook.updated",
                target=item,
                metadata={
                    "enabled": item.enabled,
                    "destination_changed": "url" in data.validated_data,
                },
            )
        return Response(subscription_data(item))


class WebhookDeliveriesView(WebhookBase):
    @extend_schema(responses=DeliveryOutput(many=True))
    def get(self, request, workspace_public_id, subscription_public_id):
        item = self.get_subscription(subscription_public_id)
        offset = history_offset(request)
        deliveries = (
            WebhookDelivery.objects.filter(subscription=item)
            .select_related("domain_event")
            .order_by("-created_at", "-pk")[offset : offset + 100]
        )
        return Response([delivery_data(row) for row in deliveries])


class WebhookInspectionView(WebhookBase):
    @extend_schema(responses=DeliveryInspection)
    def get(self, request, workspace_public_id, subscription_public_id, delivery_public_id):
        item = self.get_subscription(subscription_public_id)
        delivery = get_object_or_404(
            WebhookDelivery.objects.select_related("domain_event", "domain_event__workspace"),
            public_id=delivery_public_id,
            subscription=item,
        )
        body = delivery_body(item, delivery.domain_event)
        offset = history_offset(request)
        history = list(delivery.history.order_by("-started_at", "-pk")[offset : offset + 101])
        return Response(
            {
                **delivery_data(delivery),
                "destination": item.url,
                "next_body": body.decode(),
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "signature_scheme": "v1=HMAC-SHA256(secret, timestamp + '.' + exact UTF-8 body)",
                "history": AttemptOutput(history[:100], many=True).data,
                "history_has_more": len(history) > 100,
            }
        )


class WebhookReplayView(WebhookBase):
    @extend_schema(request=None, responses=DeliveryOutput)
    def post(self, request, workspace_public_id, subscription_public_id, delivery_public_id):
        item = self.get_subscription(subscription_public_id)
        if not item.enabled:
            raise ValidationError({"detail": "Enable the subscription before replay."})
        with transaction.atomic():
            delivery = get_object_or_404(
                WebhookDelivery.objects.select_for_update(of=("self",)).select_related(
                    "domain_event"
                ),
                public_id=delivery_public_id,
                subscription=item,
            )
            if delivery.status == WebhookDelivery.Status.PENDING:
                raise ValidationError({"detail": "Delivery is already pending."})
            delivery.status = WebhookDelivery.Status.PENDING
            delivery.attempts = 0
            delivery.next_attempt_at = None
            delivery.completed_at = None
            delivery.last_error = ""
            delivery.last_status_code = None
            delivery.save()
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="webhook.replayed",
                target=delivery,
            )
        return Response(delivery_data(delivery))
