"""Saved-view endpoints (PD-F002-B01-T02)."""

from audit.services import record_mutation
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from . import entities, query, saved_views
from .authz import has_any_role
from .entity_views import EntityPageSchema, _EntityView
from .models import SavedView
from .pagination import page_params


class SavedViewSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    entity = serializers.CharField()
    name = serializers.CharField()
    query = serializers.JSONField()
    visibility = serializers.ChoiceField(choices=SavedView.Visibility.choices)
    version = serializers.IntegerField()
    owner = serializers.CharField()
    mine = serializers.BooleanField()
    updated_at = serializers.DateTimeField()


class SavedViewInputSchema(serializers.Serializer):
    entity = serializers.CharField(required=False)
    name = serializers.CharField(max_length=80)
    query = serializers.JSONField()
    visibility = serializers.ChoiceField(choices=SavedView.Visibility.choices, required=False)
    version = serializers.IntegerField(required=False)


class SavedViewPageSchema(EntityPageSchema):
    density = serializers.CharField()
    layout = serializers.CharField()
    view = SavedViewSchema()


class _ViewBase(_EntityView):
    def may_query(self):
        return {
            key: has_any_role(self.request.user, self.get_workspace(), *entity.roles)
            for key, entity in entities.entities().items()
        }

    def visible_views(self):
        return saved_views.visible_to(
            SavedView.objects.filter(event=self.get_event()).select_related("owner"),
            self.request.user,
            self.may_query(),
        )

    def get_view(self):
        """A view the caller may see; anything else is absent, not forbidden (no existence leak)."""
        return get_object_or_404(self.visible_views(), public_id=self.kwargs["view_public_id"])

    def entity_for(self, key):
        entity = entities.get(key) if isinstance(key, str) else None
        if entity is None:
            raise ValidationError({"entity": ["Unknown entity."]})
        if not self.allowed(entity):
            raise PermissionDenied("You do not have a role that permits this action.")
        return entity


class SavedViewListView(_ViewBase):
    @extend_schema(
        parameters=[OpenApiParameter("entity", str, description="Only views of this entity.")],
        responses=SavedViewSchema(many=True),
    )
    def get(self, request, workspace_public_id, event_public_id):
        views = self.visible_views()
        entity = request.query_params.get("entity")
        if entity:
            views = views.filter(entity=entity)
        return Response([saved_views.describe(v, request.user) for v in views])

    @extend_schema(request=SavedViewInputSchema, responses={201: SavedViewSchema})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        entity = self.entity_for(request.data.get("entity"))
        view = saved_views.save(
            actor=request.user,
            workspace=self.get_workspace(),
            event=event,
            entity=entity,
            name=saved_views.validate_name(request.data.get("name")),
            definition=saved_views.normalize(entity, request.data.get("query")),
            visibility=saved_views.validate_visibility(
                request.data.get("visibility", SavedView.Visibility.PRIVATE)
            ),
        )
        return Response(saved_views.describe(view, request.user), status=201)


class SavedViewDetailView(_ViewBase):
    @extend_schema(responses=SavedViewSchema)
    def get(self, request, workspace_public_id, event_public_id, view_public_id):
        return Response(saved_views.describe(self.get_view(), request.user))

    @extend_schema(request=SavedViewInputSchema, responses=SavedViewSchema)
    def patch(self, request, workspace_public_id, event_public_id, view_public_id):
        view = self.get_view()
        if view.owner_id != request.user.pk:
            raise PermissionDenied("Only the owner can change a view.")
        entity = self.entity_for(view.entity)
        expected = request.data.get("version")
        if expected is not None and expected != view.version:
            return Response(
                {
                    "code": "view_changed",
                    "detail": "This view changed since you loaded it; reload it and apply again.",
                    "version": view.version,
                },
                status=409,
            )
        data = request.data
        updated = saved_views.save(
            actor=request.user,
            workspace=self.get_workspace(),
            event=self.get_event(),
            entity=entity,
            name=saved_views.validate_name(data.get("name", view.name)),
            definition=(
                saved_views.normalize(entity, data["query"]) if "query" in data else view.query
            ),
            visibility=saved_views.validate_visibility(data.get("visibility", view.visibility)),
            instance=view,
        )
        return Response(saved_views.describe(updated, request.user))

    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, view_public_id):
        view = self.get_view()
        is_admin = has_any_role(request.user, self.get_workspace(), "admin")
        if view.owner_id != request.user.pk and not is_admin:
            raise PermissionDenied("Only the owner or a workspace admin can delete a view.")
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="saved_view.deleted",
                target=view,
                metadata={
                    "event_id": str(view.event.public_id),
                    "entity": view.entity,
                    "name": view.name,
                    "owner": view.owner.username,
                },
            )
            view.delete()
        return Response(status=204)


class SavedViewRunView(_ViewBase):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "month", str, description="For a calendar view: 2027-03 (default: now)."
            ),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=SavedViewPageSchema,
    )
    def get(self, request, workspace_public_id, event_public_id, view_public_id):
        view = self.get_view()
        self.entity_for(view.entity)
        limit, offset = page_params(request, default=25, maximum=100)
        try:
            page = saved_views.run(
                view,
                self.get_event(),
                request.user,
                limit=limit,
                offset=offset,
                month=query.parse_month(request.query_params["month"])
                if request.query_params.get("month")
                else None,
            )
        except saved_views.ViewOutdated as exc:
            return Response({"code": "view_outdated", "detail": str(exc)}, status=409)
        return Response({**page, "view": saved_views.describe(view, request.user)})
