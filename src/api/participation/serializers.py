from rest_framework import serializers

from .models import Team, TeamInvite, TeamMembership


class TeamMembershipSerializer(serializers.ModelSerializer):
    user_public_id = serializers.UUIDField(source="user.public_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = TeamMembership
        fields = ["user_public_id", "username", "role", "joined_at"]


class TeamSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    members = TeamMembershipSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Team
        fields = ["public_id", "name", "created_at", "members"]


class TeamInviteSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = TeamInvite
        fields = [
            "public_id",
            "token",
            "created_at",
            "expires_at",
            "max_uses",
            "use_count",
            "revoked_at",
        ]
        read_only_fields = fields


class MarketplaceProfileInput(serializers.Serializer):
    skills = serializers.ListField(child=serializers.CharField(), max_length=10)
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    visible = serializers.BooleanField()


class MarketplaceProfileSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    user = serializers.UUIDField()
    username = serializers.CharField()
    skills = serializers.ListField(child=serializers.CharField())
    bio = serializers.CharField()
    visible = serializers.BooleanField()
    matched_skills = serializers.ListField(child=serializers.CharField(), required=False)


class MyMarketplaceProfileResponse(serializers.Serializer):
    profile = MarketplaceProfileSchema(allow_null=True)


class TeamOpeningInput(serializers.Serializer):
    title = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    desired_skills = serializers.ListField(child=serializers.CharField(), max_length=10)
    project = serializers.UUIDField(required=False, allow_null=True)
    is_open = serializers.BooleanField(required=False)


class TeamOpeningSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    team = serializers.UUIDField()
    team_name = serializers.CharField()
    project = serializers.UUIDField(allow_null=True)
    project_name = serializers.CharField(allow_null=True)
    title = serializers.CharField()
    description = serializers.CharField()
    desired_skills = serializers.ListField(child=serializers.CharField())
    is_open = serializers.BooleanField()
    matched_skills = serializers.ListField(child=serializers.CharField())
