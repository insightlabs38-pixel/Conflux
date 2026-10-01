"""The OpenAPI shape of an Explanation (`core.explain`), shared by every endpoint that adds one."""

from rest_framework import serializers

from . import explain


class ExplanationFixSchema(serializers.Serializer):
    destination = serializers.CharField()
    section = serializers.CharField(allow_null=True)


class ExplanationReasonSchema(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.ChoiceField(choices=explain.SEVERITIES)
    message = serializers.CharField()
    facts = serializers.DictField(required=False)
    fix = ExplanationFixSchema(required=False)


class ExplanationSchema(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=explain.OUTCOMES)
    summary = serializers.CharField()
    reasons = ExplanationReasonSchema(many=True)
    total = serializers.IntegerField()
    truncated = serializers.BooleanField()
