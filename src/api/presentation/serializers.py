from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers

from .blocks import clean_config
from .models import Page, PageBlock


class PageSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Page
        fields = ["public_id", "theme", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class PageBlockSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PageBlock
        fields = ["public_id", "kind", "position", "config", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        config = attrs.get("config", getattr(self.instance, "config", {}))
        try:
            attrs["config"] = clean_config(kind, config)
        except ModelValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return attrs
