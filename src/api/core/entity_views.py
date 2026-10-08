"""The generic, event-scoped query endpoints (PD-F002-B01-T01)."""

from accounts.authentication import CookieSessionAuthentication
from django.apps import apps
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from . import entities, query
from .authz import has_any_role
from .mixins import WorkspaceLookupMixin
from .pagination import page_params
from .permissions import IsWorkspaceMember


class EntityFieldSchema(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    type = serializers.ChoiceField(choices=list(entities.TYPES))
    operators = serializers.ListField(child=serializers.CharField())
    choices = serializers.ListField(child=serializers.CharField())
    sortable = serializers.BooleanField()
    filterable = serializers.BooleanField()
    default = serializers.BooleanField()
    groupable = serializers.BooleanField()


class EntitySchema(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    default_sort = serializers.ListField(child=serializers.CharField())
    search_fields = serializers.ListField(child=serializers.CharField())
    fields = EntityFieldSchema(many=True)


class EntityPageSchema(serializers.Serializer):
    entity = serializers.CharField()
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    filter = serializers.JSONField(allow_null=True)
    sort = serializers.ListField(child=serializers.CharField())
    search = serializers.CharField()
    columns = serializers.ListField(child=serializers.CharField())
    rows = serializers.ListField(child=serializers.DictField())
    group = serializers.CharField(required=False)
    subgroup = serializers.CharField(required=False)
    groups = serializers.ListField(child=serializers.DictField(), required=False)
    truncated = serializers.BooleanField(required=False)


def _describe(entity):
    return {
        "key": entity.key,
        "label": entity.label,
        "default_sort": list(entity.default_sort),
        "search_fields": list(entity.search_fields),
        "fields": [
            {
                "key": f.key,
                "label": f.label,
                "type": f.type,
                "operators": list(entities.OPERATORS[f.type]) if f.filterable else [],
                "choices": [str(c) for c in f.choices],
                "sortable": f.sortable,
                "filterable": f.filterable,
                "default": f.default,
                "groupable": f.groupable,
            }
            for f in entity.fields
        ],
    }


class _EntityView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_event(self):
        event_model = apps.get_model("events", "Event")
        return get_object_or_404(
            event_model,
            workspace=self.get_workspace(),
            public_id=self.kwargs["event_public_id"],
        )

    def allowed(self, entity):
        return has_any_role(self.request.user, self.get_workspace(), *entity.roles)


class EntityCatalogueView(_EntityView):
    """The entities the caller may query in this event, with each field's type and operators."""

    @extend_schema(responses=EntitySchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        self.get_event()
        return Response([_describe(e) for e in entities.entities().values() if self.allowed(e)])


class EntityQueryView(_EntityView):
    """Filter, sort and page one entity: the one list contract new features use instead of
    parsing their own query parameters."""

    @extend_schema(
        parameters=[
            OpenApiParameter("filter", str, description="Compact JSON filter tree (core.query)."),
            OpenApiParameter("sort", str, description="Comma list of fields, `-` for descending."),
            OpenApiParameter("columns", str, description="Comma list of fields to return."),
            OpenApiParameter(
                "search",
                str,
                description="Free text: every word must appear in one of the list's search fields.",
            ),
            OpenApiParameter(
                "group",
                str,
                description="A groupable field: the response lists its buckets with counts instead "
                "of rows; open a bucket with the ordinary query and its value as a condition.",
            ),
            OpenApiParameter(
                "subgroup", str, description="A second groupable field, inside each group."
            ),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=EntityPageSchema,
    )
    def get(self, request, workspace_public_id, event_public_id, entity_key):
        event = self.get_event()
        entity = entities.get(entity_key)
        if entity is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("Unknown entity.")
        if not self.allowed(entity):
            raise PermissionDenied("You do not have a role that permits this action.")
        params = request.query_params
        tree = query.parse_filter(params.get("filter"))
        order = query.parse_sort(entity, params.get("sort"))
        columns = query.parse_columns(entity, params.get("columns"))
        terms = query.parse_search(entity, params.get("search"))
        group, subgroup = query.parse_group(entity, params.get("group"), params.get("subgroup"))
        if tree:
            query.compile_filter(entity, tree)  # validate before touching the database
        limit, offset = page_params(request, default=25, maximum=100)
        if group is not None:
            buckets = query.run_groups(
                entity,
                event,
                request.user,
                tree=tree,
                search=terms,
                group=group,
                subgroup=subgroup,
            )
            return Response(
                {
                    "entity": entity.key,
                    "total": buckets["total"],
                    "limit": limit,
                    "offset": offset,
                    "filter": tree,
                    "sort": order,
                    "search": " ".join(terms),
                    "columns": [f.key for f in columns],
                    "rows": [],
                    "group": group.key,
                    **({"subgroup": subgroup.key} if subgroup else {}),
                    "groups": buckets["groups"],
                    "truncated": buckets["truncated"],
                }
            )
        result = query.run(
            entity,
            event,
            request.user,
            tree=tree,
            sort=order,
            columns=columns,
            limit=limit,
            offset=offset,
            search=terms,
        )
        return Response(
            {
                "entity": entity.key,
                "total": result["total"],
                "limit": limit,
                "offset": offset,
                "filter": tree,
                "sort": order,
                "search": " ".join(terms),
                "columns": [f.key for f in columns],
                "rows": result["rows"],
            }
        )
