from rest_framework import serializers


class GalleryProjectSchema(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    summary = serializers.CharField(allow_blank=True)
    team = serializers.CharField()
    track = serializers.CharField()
    repo_url = serializers.URLField()


class JudgeScoreSchema(serializers.Serializer):
    project = serializers.CharField()
    comment = serializers.CharField(allow_blank=True)
    criteria = serializers.DictField(child=serializers.IntegerField())


class ErrorSchema(serializers.Serializer):
    detail = serializers.CharField()
