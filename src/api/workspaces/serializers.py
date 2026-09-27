from rest_framework import serializers


class WorkspaceSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.SlugField()


class WorkspaceInputSchema(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField(required=False)


class MembershipSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    user = serializers.CharField()
    role = serializers.CharField()


class MembershipInputSchema(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.CharField()
