"""Saved views: named, shareable definitions of how to look at one entity (PD-F002-B01-T02).

A view stores a query definition only. Saving validates it against the entity it names, running it
goes through `core.query` under the viewer's own authorization, and sharing widens who may *see
the definition*, never what rows anyone may see.
"""

from audit.services import diff_snapshots, record_mutation
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from . import entities, query
from .models import SavedView

MAX_PER_OWNER = 50
DENSITIES = ("compact", "comfortable")
_KEYS = {"filter", "sort", "columns", "density", "search"}


class ViewOutdated(Exception):
    """The stored definition no longer fits the entity (a field was renamed or removed)."""


def normalize(entity, raw):
    """Validate a client's definition against the entity and return the canonical stored form."""
    if not isinstance(raw, dict):
        raise ValidationError({"query": ["A view's query is an object."]})
    extra = raw.keys() - _KEYS
    if extra:
        raise ValidationError({"query": [f"Unknown keys: {', '.join(sorted(map(str, extra)))}."]})
    tree = raw.get("filter")
    if tree is not None:
        query.compile_filter(entity, tree)
    sort = raw.get("sort") or ""
    if not isinstance(sort, str):
        raise ValidationError({"sort": ["Sort is a comma list of fields."]})
    query.parse_sort(entity, sort)
    columns = raw.get("columns") or []
    if not isinstance(columns, list) or not all(isinstance(c, str) for c in columns):
        raise ValidationError({"columns": ["Columns is a list of field keys."]})
    query.parse_columns(entity, ",".join(columns))
    search = raw.get("search") or ""
    if not isinstance(search, str):
        raise ValidationError({"search": ["Search is text."]})
    terms = query.parse_search(entity, search)
    density = raw.get("density") or "comfortable"
    if density not in DENSITIES:
        raise ValidationError({"density": [f"Use one of {', '.join(DENSITIES)}."]})
    definition = {
        "filter": tree or None,
        "sort": sort,
        "columns": columns,
        "density": density,
    }
    if terms:  # additive (PD-F006-B01-T02): stored only when used, so older views are unchanged
        definition["search"] = " ".join(terms)
    return definition


def validate_visibility(value):
    if value not in SavedView.Visibility.values:
        raise ValidationError(
            {"visibility": [f"Use one of {', '.join(SavedView.Visibility.values)}."]}
        )
    return value


def validate_name(value):
    name = value.strip() if isinstance(value, str) else ""
    if not name or len(name) > 80:
        raise ValidationError({"name": ["A view needs a name of 1 to 80 characters."]})
    return name


def visible_to(queryset, user, may_query):
    """Views the user may see: their own, and organizers' views for entities they may query."""
    from django.db.models import Q

    allowed = [key for key, permitted in may_query.items() if permitted]
    return queryset.filter(entity__in=allowed).filter(
        Q(owner=user) | Q(visibility=SavedView.Visibility.ORGANIZERS)
    )


def describe(view, user):
    return {
        "public_id": str(view.public_id),
        "entity": view.entity,
        "name": view.name,
        "query": view.query,
        "visibility": view.visibility,
        "version": view.version,
        "owner": view.owner.username,
        "mine": view.owner_id == user.pk,
        "updated_at": view.updated_at.isoformat().replace("+00:00", "Z"),
    }


def save(*, actor, workspace, event, entity, name, definition, visibility, instance=None):
    """Create or update under a lock; audits without copying filter values (they can hold personal
    data) into the record."""
    try:
        with transaction.atomic():
            if instance is None:
                taken = SavedView.objects.filter(event=event, owner=actor).count()
                if taken >= MAX_PER_OWNER:
                    raise ValidationError(
                        {"name": [f"You can keep at most {MAX_PER_OWNER} views per event."]}
                    )
                view = SavedView.objects.create(
                    event=event,
                    owner=actor,
                    entity=entity.key,
                    name=name,
                    query=definition,
                    visibility=visibility,
                )
                record_mutation(
                    actor=actor,
                    workspace=workspace,
                    action="saved_view.created",
                    target=view,
                    metadata={
                        "event_id": str(event.public_id),
                        "entity": entity.key,
                        "name": name,
                        "visibility": visibility,
                    },
                )
                return view
            view = SavedView.objects.select_for_update().get(pk=instance.pk)
            before = {"name": view.name, "visibility": view.visibility}
            query_changed = view.query != definition
            view.name, view.visibility, view.query = name, visibility, definition
            view.version += 1
            view.save()
            metadata = {"event_id": str(event.public_id), "entity": entity.key}
            changes = diff_snapshots(before, {"name": view.name, "visibility": view.visibility})
            if changes:
                metadata["changes"] = changes
            if query_changed:
                metadata["query_changed"] = True
            record_mutation(
                actor=actor,
                workspace=workspace,
                action="saved_view.updated",
                target=view,
                metadata=metadata,
            )
            return view
    except IntegrityError as exc:
        raise ValidationError({"name": ["You already have a view with this name."]}) from exc


def run(view, event, user, *, limit, offset):
    """The view's page under the viewer's authorization; a definition that no longer fits is
    reported, never silently loosened."""
    entity = entities.get(view.entity)
    if entity is None:
        raise ViewOutdated("This view's entity is no longer available.")
    try:
        definition = normalize(entity, view.query)
        tree = definition["filter"]
        order = query.parse_sort(entity, definition["sort"])
        columns = query.parse_columns(entity, ",".join(definition["columns"]))
        terms = query.parse_search(entity, definition.get("search"))
    except ValidationError as exc:
        raise ViewOutdated(
            "; ".join(f"{key}: {' '.join(map(str, value))}" for key, value in exc.detail.items())
        ) from exc
    result = query.run(
        entity,
        event,
        user,
        tree=tree,
        sort=order,
        columns=columns,
        limit=limit,
        offset=offset,
        search=terms,
    )
    return {
        "entity": entity.key,
        "total": result["total"],
        "limit": limit,
        "offset": offset,
        "filter": tree,
        "sort": order,
        "search": " ".join(terms),
        "columns": [f.key for f in columns],
        "rows": result["rows"],
        "density": definition["density"],
    }
