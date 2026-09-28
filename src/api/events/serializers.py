from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from .models import (
    Announcement,
    BasePrize,
    Event,
    EventApplication,
    EventRegistrationSettings,
    EventStatus,
    ParticipantCheckIn,
    RegistrationInviteCode,
    RegistrationStatus,
    Track,
)


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


class AnnouncementSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    posted_by = serializers.CharField(source="posted_by.username", read_only=True)

    class Meta:
        model = Announcement
        fields = ["public_id", "title", "body", "posted_by", "created_at", "hidden_at", "version"]
        read_only_fields = ["public_id", "posted_by", "created_at", "hidden_at", "version"]


class RegistrationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistrationSettings
        fields = ["mode", "capacity", "waitlist_enabled", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_capacity(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Capacity must be at least 1.")
        return value


class RegistrationInviteCodeSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = RegistrationInviteCode
        fields = ["public_id", "code", "max_uses", "use_count", "created_at", "revoked_at"]
        read_only_fields = ["public_id", "code", "use_count", "created_at", "revoked_at"]


class ApplyToEventInputSchema(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
    code = serializers.CharField(required=False, allow_blank=True, max_length=32)


class EventApplicationSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    user = serializers.UUIDField(source="user.public_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    decided_by = serializers.UUIDField(
        source="decided_by.public_id", read_only=True, allow_null=True
    )

    class Meta:
        model = EventApplication
        fields = [
            "public_id",
            "user",
            "username",
            "status",
            "note",
            "waitlist_position",
            "decided_by",
            "decided_at",
            "created_at",
        ]
        read_only_fields = fields


class MyEventApplicationResponse(serializers.Serializer):
    application = EventApplicationSerializer(allow_null=True)


class ApplicationDecisionInputSchema(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            RegistrationStatus.APPROVED,
            RegistrationStatus.WAITLISTED,
            RegistrationStatus.REJECTED,
        ]
    )


class CheckInInputSchema(serializers.Serializer):
    participant = serializers.UUIDField()


class CheckInSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    participant = serializers.UUIDField(source="participant.public_id", read_only=True)
    participant_username = serializers.CharField(source="participant.username", read_only=True)
    checked_in_by = serializers.CharField(source="checked_in_by.username", read_only=True)

    class Meta:
        model = ParticipantCheckIn
        fields = [
            "public_id",
            "participant",
            "participant_username",
            "checked_in_by",
            "checked_in_at",
        ]
        read_only_fields = fields
