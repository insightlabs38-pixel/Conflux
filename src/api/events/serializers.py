from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from .models import BasePrize, Event, EventStatus, Track


class EventSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    status = serializers.ChoiceField(choices=EventStatus.choices, read_only=True)

    class Meta:
        model = Event
        fields = [
            "public_id",
            "name",
            "slug",
            "description",
            "timezone",
            "starts_at",
            "ends_at",
            "status",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise serializers.ValidationError("Use a valid IANA timezone.") from exc
        return value

    def validate(self, attrs):
        start = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        end = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if start and end and start >= end:
            raise serializers.ValidationError({"ends_at": "End must be after start."})
        return attrs


class TrackSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Track
        fields = ["public_id", "name", "description", "position"]


class BasePrizeSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    track = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = BasePrize
        fields = [
            "public_id",
            "name",
            "description",
            "kind",
            "amount",
            "currency",
            "track",
            "position",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["track"] = str(instance.track.public_id) if instance.track_id else None
        return data

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        amount = attrs.get("amount", getattr(self.instance, "amount", None))
        currency = attrs.get("currency", getattr(self.instance, "currency", ""))
        if kind == BasePrize.Kind.CASH and (amount is None or not currency):
            raise serializers.ValidationError(
                {"amount": "Cash prizes require an amount and currency."}
            )
        if kind != BasePrize.Kind.CASH and (amount is not None or currency):
            raise serializers.ValidationError(
                {"amount": "Only cash prizes may have an amount or currency."}
            )
        if amount is not None and amount < 0:
            raise serializers.ValidationError({"amount": "Amount must be nonnegative."})
        if currency and (len(currency) != 3 or not currency.isalpha()):
            raise serializers.ValidationError({"currency": "Use a three-letter currency code."})
        return attrs
