from rest_framework import serializers

from .models import MentorNote, Project, ProjectMembership


class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField(source="user.public_id", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ["user", "role", "joined_at"]


class ProjectSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    team = serializers.UUIDField(source="team.public_id", read_only=True, allow_null=True)
    track = serializers.UUIDField(source="track.public_id", read_only=True, allow_null=True)
    members = ProjectMembershipSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "public_id",
            "name",
            "description",
            "team",
            "track",
            "created_at",
            "updated_at",
            "members",
        ]


class MentorNoteInputSchema(serializers.Serializer):
    body = serializers.CharField(max_length=1000)


class MentorNoteSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    mentor = serializers.UUIDField(source="mentor.public_id", read_only=True)
    mentor_username = serializers.CharField(source="mentor.username", read_only=True)

    class Meta:
        model = MentorNote
        fields = ["public_id", "mentor", "mentor_username", "body", "created_at"]
        read_only_fields = ["public_id", "mentor", "mentor_username", "created_at"]


class SponsorProjectSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    team_name = serializers.CharField(allow_null=True)
    track_name = serializers.CharField(allow_null=True)
