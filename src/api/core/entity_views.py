"""The generic, event-scoped query endpoints (PD-F002-B01-T01)."""

from accounts.authentication import CookieSessionAuthentication
from django.apps import apps
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
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
    layouts = serializers.ListField(child=serializers.CharField())
    board_field = serializers.CharField()
    calendar_fields = serializers.ListField(child=serializers.CharField())
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
    calendar = serializers.CharField(required=False)
    month = serializers.CharField(required=False)
    days = serializers.ListField(child=serializers.DictField(), required=False)


def _describe(entity):
    return {
        "key": entity.key,
        "label": entity.label,
        "default_sort": list(entity.default_sort),
        "search_fields": list(entity.search_fields),
        "layouts": entity.layouts(),
        "board_field": entity.board_field,
        "calendar_fields": list(entity.calendar_fields),
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
            OpenApiParameter(
                "calendar",
                str,
                description="A date field of a list that has a calendar: the response lists the "
                "days of `month` with counts instead of rows; open a day with the ordinary query "
                "and the day as conditions.",
            ),
            OpenApiParameter("month", str, description="With `calendar`: 2027-03 (default: now)."),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=EntityPageSchema,
    )
    def get(self, request, workspace_public_id, event_public_id, entity_key):
        event = self.get_event()
        entity = entities.get(entity_key)
        if entity is None:
            raise NotFound("Unknown entity.")
        if not self.allowed(entity):
            raise PermissionDenied("You do not have a role that permits this action.")
        params = request.query_params
        tree = query.parse_filter(params.get("filter"))
        order = query.parse_sort(entity, params.get("sort"))
        columns = query.parse_columns(entity, params.get("columns"))
        terms = query.parse_search(entity, params.get("search"))
        group, subgroup = query.parse_group(entity, params.get("group"), params.get("subgroup"))
        calendar = month = None
        if params.get("calendar"):
            if group is not None:
                raise query.QueryError("", "A calendar cannot also be grouped.", root="calendar")
            _, calendar = query.parse_layout(entity, "calendar", params.get("calendar"))
            month = query.parse_month(params.get("month"))
        if tree:
            query.compile_filter(entity, tree)  # validate before touching the database
        limit, offset = page_params(request, default=25, maximum=100)
        return Response(
            query.answer(
                entity,
                event,
                request.user,
                tree=tree,
                order=order,
                columns=columns,
                terms=terms,
                group=group,
                subgroup=subgroup,
                calendar=calendar,
                month=month,
                limit=limit,
                offset=offset,
            )
        )


class EntityRowSchema(serializers.Serializer):
    entity = serializers.CharField()
    row = serializers.DictField()


class EntityRowView(_EntityView):
    """One record of a list with every field, for the inspector: whatever the list's own query
    would let this person see, found by its public id and absent otherwise."""

    @extend_schema(responses=EntityRowSchema)
    def get(self, request, workspace_public_id, event_public_id, entity_key, row_public_id):
        event = self.get_event()
        entity = entities.get(entity_key)
        if entity is None:
            raise NotFound("Unknown entity.")
        if not self.allowed(entity):
            raise PermissionDenied("You do not have a role that permits this action.")
        row = query.one(entity, event, request.user, row_public_id)
        if row is None:
            raise NotFound("No such record.")
        return Response({"entity": entity.key, "row": row})
