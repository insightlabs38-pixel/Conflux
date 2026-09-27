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
