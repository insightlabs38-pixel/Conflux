from rest_framework import serializers


class MembershipSummarySchema(serializers.Serializer):
    workspace = serializers.UUIDField()
    workspace_name = serializers.CharField()
    workspace_slug = serializers.CharField()
    role = serializers.CharField()


class UserSummarySchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    username = serializers.CharField()
    memberships = MembershipSummarySchema(many=True)


class LoginInputSchema(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSchema(serializers.Serializer):
    user = UserSummarySchema()


class ProfileLinkSchema(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {"label", "url"}:
            raise serializers.ValidationError("Each link needs only a label and URL.")
        return super().to_internal_value(data)

    label = serializers.CharField(max_length=50)
    url = serializers.URLField(max_length=2048)


class UserProfileSerializer(serializers.ModelSerializer):
    links = ProfileLinkSchema(many=True, required=False)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=40), max_length=12, required=False
    )
    interests = serializers.ListField(
        child=serializers.CharField(max_length=40), max_length=12, required=False
    )
    preferred_roles = serializers.ListField(
        child=serializers.CharField(max_length=40), max_length=12, required=False
    )

    class Meta:
        from .models import UserProfile

        model = UserProfile
        fields = [
            "display_name",
            "avatar_url",
            "bio",
            "location",
            "links",
            "visibility",
            "skills",
            "interests",
            "preferred_roles",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_avatar_url(self, value):
        from django.core.exceptions import ValidationError

        from .profile import safe_profile_url

        try:
            return safe_profile_url(value, allow_blank=True)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_links(self, value):
        from django.core.exceptions import ValidationError

        from .profile import clean_links

        try:
            return clean_links(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def _tags(self, value):
        from django.core.exceptions import ValidationError

        from .profile import clean_tags

        try:
            return clean_tags(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    validate_skills = _tags
    validate_interests = _tags
    validate_preferred_roles = _tags
