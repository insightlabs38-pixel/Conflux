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
