"""Thread endpoints (PD-F002-B01-T07). Who may read or write is decided by the registered subject
and audience (`core.threads`), never by the client; everything else is 404."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.response import Response

from . import threads
from .entity_views import _EntityView
from .idempotency import IdempotentMixin
from .pagination import page_params


class ThreadAuthorSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    username = serializers.CharField()


class ThreadCommentSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    author = ThreadAuthorSchema()
    body = serializers.CharField(allow_blank=True)
    removed = serializers.BooleanField()
    edited = serializers.BooleanField()
    mentions = serializers.ListField(child=serializers.CharField())
    created_at = serializers.DateTimeField()
    can_edit = serializers.BooleanField()
    can_remove = serializers.BooleanField()
    replies = serializers.ListField(child=serializers.DictField())


class ThreadSubjectSchema(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.CharField()
    label = serializers.CharField()


class ThreadSchema(serializers.Serializer):
    subject = ThreadSubjectSchema()
    audience = serializers.CharField()
    can_post = serializers.BooleanField()
    total = serializers.IntegerField()
    comments = ThreadCommentSchema(many=True)


class CommentInput(serializers.Serializer):
    body = serializers.CharField(max_length=threads.MAX_BODY * 2)
    parent = serializers.UUIDField(required=False)


class CommentEditInput(serializers.Serializer):
    body = serializers.CharField(max_length=threads.MAX_BODY * 2)


class _ThreadView(_EntityView):
    pass


class ThreadView(IdempotentMixin, _ThreadView):
    def target(self):
        return threads.resolve(
            self.get_event(),
            self.request.user,
            self.kwargs["subject_type"],
            self.kwargs["subject_id"],
            self.kwargs["audience"],
        )

    @extend_schema(
        parameters=[OpenApiParameter("limit", int), OpenApiParameter("offset", int)],
        responses=ThreadSchema,
    )
    def get(self, request, **kwargs):
        limit, offset = page_params(request, default=50, maximum=100)
        return Response(threads.view(self.target(), request.user, limit, offset))

    @extend_schema(request=CommentInput, responses={201: ThreadCommentSchema})
    def post(self, request, **kwargs):
        data = CommentInput(data=request.data)
        data.is_valid(raise_exception=True)
        target = self.target()
        comment = threads.post(
            target,
            request.user,
            data.validated_data["body"],
            data.validated_data.get("parent"),
        )
        return Response(threads.describe_comment(comment, request.user, target), status=201)


class ThreadCommentView(IdempotentMixin, _ThreadView):
    @extend_schema(request=CommentEditInput, responses=ThreadCommentSchema)
    def patch(self, request, workspace_public_id, event_public_id, comment_public_id):
        data = CommentEditInput(data=request.data)
        data.is_valid(raise_exception=True)
        event = self.get_event()
        comment = threads.edit(event, request.user, comment_public_id, data.validated_data["body"])
        _, target = threads.comment_target(event, request.user, comment_public_id)
        return Response(threads.describe_comment(comment, request.user, target))

    @extend_schema(request=None, responses=ThreadCommentSchema)
    def delete(self, request, workspace_public_id, event_public_id, comment_public_id):
        event = self.get_event()
        comment = threads.remove(event, request.user, comment_public_id)
        _, target = threads.comment_target(event, request.user, comment_public_id)
        return Response(threads.describe_comment(comment, request.user, target))
