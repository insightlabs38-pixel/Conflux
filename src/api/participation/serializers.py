from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Team, TeamInvite, TeamMembership


class TeamMembershipSerializer(serializers.ModelSerializer):
    user_public_id = serializers.UUIDField(source="user.public_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    identity = serializers.SerializerMethodField()

    @extend_schema_field(serializers.JSONField())
    def get_identity(self, obj):
        from accounts.profile import identity_for

        return identity_for(obj.user, workspace=obj.team.event.workspace)

    class Meta:
        model = TeamMembership
        fields = ["user_public_id", "username", "identity", "role", "joined_at"]


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
    roles = serializers.ListField(child=serializers.CharField(), max_length=10, required=False)
    interests = serializers.ListField(child=serializers.CharField(), max_length=10, required=False)
    availability_hours_per_week = serializers.IntegerField(
        min_value=0, max_value=168, required=False, allow_null=True
    )
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    visible = serializers.BooleanField()


class MarketplaceProfileSchema(serializers.Serializer):
    identity = serializers.JSONField()
    public_id = serializers.UUIDField()
    user = serializers.UUIDField()
    username = serializers.CharField()
    skills = serializers.ListField(child=serializers.CharField())
    roles = serializers.ListField(child=serializers.CharField())
    interests = serializers.ListField(child=serializers.CharField())
    availability_hours_per_week = serializers.IntegerField(allow_null=True)
    bio = serializers.CharField()
    visible = serializers.BooleanField()
    matched_skills = serializers.ListField(child=serializers.CharField(), required=False)
    matched_roles = serializers.ListField(child=serializers.CharField(), required=False)
    matched_interests = serializers.ListField(child=serializers.CharField(), required=False)
    availability_compatible = serializers.BooleanField(required=False, allow_null=True)


class MyMarketplaceProfileResponse(serializers.Serializer):
    profile = MarketplaceProfileSchema(allow_null=True)


class TeamOpeningInput(serializers.Serializer):
    title = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    desired_skills = serializers.ListField(child=serializers.CharField(), max_length=10)
    desired_roles = serializers.ListField(
        child=serializers.CharField(), max_length=10, required=False
    )
    interests = serializers.ListField(child=serializers.CharField(), max_length=10, required=False)
    min_availability_hours_per_week = serializers.IntegerField(
        min_value=0, max_value=168, required=False, allow_null=True
    )
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
    desired_roles = serializers.ListField(child=serializers.CharField())
    interests = serializers.ListField(child=serializers.CharField())
    min_availability_hours_per_week = serializers.IntegerField(allow_null=True)
    is_open = serializers.BooleanField()
    matched_skills = serializers.ListField(child=serializers.CharField())
    matched_roles = serializers.ListField(child=serializers.CharField(), required=False)
    matched_interests = serializers.ListField(child=serializers.CharField(), required=False)
    availability_compatible = serializers.BooleanField(required=False, allow_null=True)
