from rest_framework import serializers

from .models import Project, ProjectMembership


class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField(source="user.public_id", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ["user", "role", "joined_at"]


class ProjectSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    team = serializers.UUIDField(source="team.public_id", read_only=True, allow_null=True)
    members = ProjectMembershipSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["public_id", "name", "description", "team", "created_at", "updated_at", "members"]
