from rest_framework import serializers


class ReadinessFixSchema(serializers.Serializer):
    destination = serializers.CharField()
    section = serializers.CharField(allow_blank=True)


class ReadinessItemSchema(serializers.Serializer):
    id = serializers.CharField()
    severity = serializers.ChoiceField(choices=["blocker", "warning"])
    passed = serializers.BooleanField()
    detail = serializers.CharField()
    module = serializers.CharField()
    fix = ReadinessFixSchema()


class ReadinessSchema(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ready", "warning", "blocked"])
    items = ReadinessItemSchema(many=True)
