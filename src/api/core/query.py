"""Compile a client query against a registered entity (PD-F002-B01-T01).

The query is data: a versioned JSON filter tree, a sort list and a column list. It is validated
against the entity's registered fields and operators and compiled to ORM expressions; no lookup
string, relation traversal or SQL ever comes from the client. Every refusal names the offending
part by its path (`and[1].op`) so a client can fix it. Stateless: nothing here is stored.
"""

import json
import math
import re
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID as UuidValue

from django.db.models import Count, F, Q
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.exceptions import ValidationError

from .entities import BOOL, DATE, ENUM, LAYOUTS, NUMBER, OPERATORS, TEXT, UUID, Entity

VERSION = 1
MAX_DEPTH = 4
MAX_PREDICATES = 20
MAX_IN = 50
MAX_TEXT = 200
MAX_SORT = 3
MAX_GROUPS = 200
MAX_TERMS = 5
MIN_TERM = 2


class QueryError(ValidationError):
    """A 400 keyed by the path of the offending part: `{"filter.and[1].op": ["..."]}`."""

    def __init__(self, path, message, root="filter"):
        super().__init__({f"{root}.{path}" if path else root: [message]})


def parse_filter(raw):
    """The `filter` query parameter: compact JSON, or empty for no filter."""
    if raw in (None, ""):
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise QueryError("", "The filter must be valid JSON.") from exc


def canonical(filter_tree):
    """The one text form of a filter (sorted keys, no spaces): what URLs and saved views store."""
    return json.dumps(filter_tree, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class _Budget:
    def __init__(self):
        self.predicates = 0


def _scalar(field, op, value, path):
    if value is None:
        raise QueryError(path, f"A value is required for {op}.")
    if field.type == TEXT:
        if not isinstance(value, str):
            raise QueryError(path, "A text field compares with text.")
        if len(value) > MAX_TEXT:
            raise QueryError(path, f"Text values are limited to {MAX_TEXT} characters.")
        return value
    if field.type == NUMBER:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise QueryError(path, "A number field compares with a number.")
        if not math.isfinite(value):
            raise QueryError(path, "A number must be finite.")
        return value
    if field.type == BOOL:
        if not isinstance(value, bool):
            raise QueryError(path, "A yes/no field compares with true or false.")
        return value
    if field.type == ENUM:
        if value not in field.choices:
            raise QueryError(path, f"Use one of {', '.join(map(str, field.choices))}.")
        return value
    if field.type == UUID:
        try:
            return UuidValue(str(value))
        except (ValueError, AttributeError) as exc:
            raise QueryError(path, "Not a valid id.") from exc
    if field.type == DATE:
        return _instant(value, path)
    raise QueryError(path, "Unsupported field type.")  # pragma: no cover


def _instant(value, path):
    if not isinstance(value, str):
        raise QueryError(
            path, "A date is an ISO 8601 text such as 2027-03-05 or 2027-03-05T09:00:00Z."
        )
    parsed = parse_datetime(value)
    if parsed is None:
        day = parse_date(value)
        if day is None:
            raise QueryError(path, "Not an ISO 8601 date or date-time.")
        parsed = datetime.combine(day, time.min)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _predicate(entity: Entity, node, path, budget):
    budget.predicates += 1
    if budget.predicates > MAX_PREDICATES:
        raise QueryError(path, f"At most {MAX_PREDICATES} conditions are allowed.")
    extra = node.keys() - {"field", "op", "value"}
    if extra:
        raise QueryError(path, f"Unknown keys: {', '.join(sorted(map(str, extra)))}.")
    key, op = node.get("field"), node.get("op")
    field = entity.field(key) if isinstance(key, str) else None
    if field is None or not field.filterable:
        names = ", ".join(f.key for f in entity.fields if f.filterable)
        raise QueryError(
            f"{path}.field" if path else "field", f"Unknown field {key!r}; use one of {names}."
        )
    allowed = OPERATORS[field.type]
    if op not in allowed:
        raise QueryError(
            f"{path}.op" if path else "op",
            f"{field.type} field {field.key!r} does not support {op!r}; use {', '.join(allowed)}.",
        )
    where = f"{path}.value" if path else "value"
    column, value = field.column, node.get("value")
    if op == "is_null":
        if not isinstance(value, bool):
            raise QueryError(where, "is_null takes true or false.")
        return Q(**{f"{column}__isnull": value})
    if op == "in":
        if not isinstance(value, list) or not value:
            raise QueryError(where, "in takes a non-empty list.")
        if len(value) > MAX_IN:
            raise QueryError(where, f"At most {MAX_IN} values are allowed.")
        return Q(**{f"{column}__in": [_scalar(field, op, v, where) for v in value]})
    if op == "between":
        if not isinstance(value, list) or len(value) != 2:
            raise QueryError(where, "between takes [low, high].")
        low, high = (_scalar(field, op, v, where) for v in value)
        return Q(**{f"{column}__gte": low, f"{column}__lte": high})
    value = _scalar(field, op, value, where)
    lookup = {
        "eq": "exact",
        "ne": "exact",
        "lt": "lt",
        "lte": "lte",
        "gt": "gt",
        "gte": "gte",
        "contains": "icontains",
        "startswith": "istartswith",
    }[op]
    q = Q(**{f"{column}__{lookup}": value})
    return ~q if op == "ne" else q


def _node(entity: Entity, node, path, depth, budget):
    if not isinstance(node, dict):
        raise QueryError(path, "A condition is an object.")
    groups = [k for k in ("and", "or", "not") if k in node]
    if groups:
        if len(node) != 1:
            raise QueryError(path, "A group has only one of and, or, not.")
        if depth >= MAX_DEPTH:
            raise QueryError(path, f"Groups are nested at most {MAX_DEPTH} deep.")
        kind = groups[0]
        inner = node[kind]
        if kind == "not":
            return ~_node(entity, inner, f"{path}.not" if path else "not", depth + 1, budget)
        if not isinstance(inner, list) or not inner:
            raise QueryError(f"{path}.{kind}" if path else kind, f"{kind} takes a non-empty list.")
        parts = [
            _node(
                entity, child, f"{path}.{kind}[{i}]" if path else f"{kind}[{i}]", depth + 1, budget
            )
            for i, child in enumerate(inner)
        ]
        combined = parts[0]
        for part in parts[1:]:
            combined = combined & part if kind == "and" else combined | part
        return combined
    return _predicate(entity, node, path, budget)


def compile_filter(entity: Entity, tree):
    """A `Q` for the filter tree (empty tree: no restriction)."""
    if tree is None or tree == {}:
        return Q()
    return _node(entity, tree, "", 0, _Budget())


def parse_search(entity: Entity, raw):
    """The `search` parameter as its terms: whitespace separated, every one must match."""
    if raw is None or not str(raw).strip():
        return []
    if not entity.search_fields:
        raise QueryError("", "This list cannot be searched.", root="search")
    terms = str(raw).split()
    if len(terms) > MAX_TERMS:
        raise QueryError("", f"Search takes at most {MAX_TERMS} words.", root="search")
    for index, term in enumerate(terms):
        if len(term) < MIN_TERM:
            raise QueryError(
                f"[{index}]",
                f"Each search word needs at least {MIN_TERM} characters.",
                root="search",
            )
        if len(term) > MAX_TEXT:
            raise QueryError(
                f"[{index}]", f"Search words are limited to {MAX_TEXT} characters.", root="search"
            )
    return terms


def compile_search(entity: Entity, terms):
    """Every term must appear in at least one of the entity's search fields (case-insensitive)."""
    combined = Q()
    for term in terms:
        any_field = Q()
        for key in entity.search_fields:
            any_field |= Q(**{f"{entity.field(key).column}__icontains": term})
        combined &= any_field
    return combined


def parse_sort(entity: Entity, raw):
    """`name,-created_at` -> ORM ordering with the entity default and a primary-key tiebreak."""
    keys = [part.strip() for part in (raw or "").split(",") if part.strip()]
    if len(keys) > MAX_SORT:
        raise QueryError("", f"Sort by at most {MAX_SORT} fields.", root="sort")
    order = []
    for part in keys:
        name, descending = (part[1:], True) if part.startswith("-") else (part, False)
        field = entity.field(name)
        if field is None or not field.sortable:
            names = ", ".join(f.key for f in entity.fields if f.sortable)
            raise QueryError("", f"Cannot sort by {name!r}; use one of {names}.", root="sort")
        order.append(("-" if descending else "") + field.column)
    return order or list(entity.default_sort)


def parse_group(entity: Entity, group, subgroup):
    """`group` and `subgroup` as fields: both groupable, different, and a subgroup needs a group."""
    found = []
    for root, key in (("group", group), ("subgroup", subgroup)):
        if not key:
            found.append(None)
            continue
        field = entity.field(key)
        if field is None or not field.groupable:
            names = ", ".join(f.key for f in entity.fields if f.groupable) or "none"
            raise QueryError("", f"Cannot group by {key!r}; use one of {names}.", root=root)
        found.append(field)
    if found[1] is not None and found[0] is None:
        raise QueryError("", "A subgroup needs a group.", root="subgroup")
    if found[1] is not None and found[1] is found[0]:
        raise QueryError("", "The subgroup must differ from the group.", root="subgroup")
    return found[0], found[1]


def parse_layout(entity: Entity, layout, calendar):
    """A saved layout and the date field of a calendar, checked against what the entity offers."""
    layout = layout or "list"
    if layout not in LAYOUTS:
        raise QueryError("", f"Use one of {', '.join(LAYOUTS)}.", root="layout")
    if layout not in entity.layouts():
        raise QueryError(
            "",
            f"This list has no {layout} layout; use one of {', '.join(entity.layouts())}.",
            root="layout",
        )
    if layout != "calendar":
        if calendar:
            raise QueryError("", "Only a calendar names a date field.", root="calendar")
        return layout, None
    key = calendar or entity.calendar_fields[0]
    if key not in entity.calendar_fields:
        raise QueryError(
            "",
            f"Cannot place rows by {key!r}; use {', '.join(entity.calendar_fields)}.",
            root="calendar",
        )
    return layout, entity.field(key)


_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def parse_month(raw):
    """`2027-03` -> the first instant of that month and of the next, in UTC; empty is this month."""
    if raw in (None, ""):
        today = datetime.now(UTC)
        year, month = today.year, today.month
    else:
        found = _MONTH.match(str(raw))
        if not found or not 1970 <= int(found.group(1)) <= 2200:
            raise QueryError("", "A month is written 2027-03.", root="month")
        year, month = int(found.group(1)), int(found.group(2))
    start = datetime(year, month, 1, tzinfo=UTC)
    following = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=UTC)
    return f"{year:04d}-{month:02d}", start, following


def _label(field, value):
    if value is None:
        return "(none)"
    if field.type == BOOL:
        return "Yes" if value else "No"
    return str(_plain(value))


def run_groups(entity: Entity, event, user, *, tree, search, group, subgroup):
    """The buckets of the current result: one per value of `group` (and of `subgroup` inside it),
    each with its count, empty values last. No rows - a bucket is opened with the ordinary query
    and the bucket's value as one more condition, so there is one way to read rows."""
    queryset = entity.base(event, user)
    if tree:
        queryset = queryset.filter(compile_filter(entity, tree))
    if search:
        queryset = queryset.filter(compile_search(entity, search))
    columns = [group.column] + ([subgroup.column] if subgroup else [])
    buckets = (
        queryset.order_by()
        .values(*columns)
        .annotate(n=Count("pk"))
        .order_by(*[F(column).asc(nulls_last=True) for column in columns])
    )
    groups, truncated = [], False
    for row in buckets:
        value = row[group.column]
        if not groups or groups[-1]["_raw"] != value:
            if len(groups) >= MAX_GROUPS:
                truncated = True
                break
            groups.append(
                {
                    "_raw": value,
                    "key": _plain(value),
                    "label": _label(group, value),
                    "null": value is None,
                    "count": 0,
                    **({"subgroups": []} if subgroup else {}),
                }
            )
        groups[-1]["count"] += row["n"]
        if subgroup:
            sub = row[subgroup.column]
            groups[-1]["subgroups"].append(
                {
                    "key": _plain(sub),
                    "label": _label(subgroup, sub),
                    "null": sub is None,
                    "count": row["n"],
                }
            )
    for item in groups:
        del item["_raw"]
    return {"groups": groups, "truncated": truncated, "total": sum(g["count"] for g in groups)}


def run_days(entity: Entity, event, user, *, tree, search, field, month):
    """The rows of one month placed on days: a count per calendar day (UTC) for the current filter
    and search. No rows - a day is opened with the ordinary query and the day as two conditions."""
    label, start, following = month
    queryset = entity.base(event, user)
    if tree:
        queryset = queryset.filter(compile_filter(entity, tree))
    if search:
        queryset = queryset.filter(compile_search(entity, search))
    queryset = queryset.filter(**{f"{field.column}__gte": start, f"{field.column}__lt": following})
    days = (
        queryset.order_by()
        .annotate(_day=TruncDate(field.column, tzinfo=UTC))
        .values("_day")
        .annotate(n=Count("pk"))
        .order_by("_day")
    )
    found = [{"date": row["_day"].isoformat(), "count": row["n"]} for row in days]
    return {"month": label, "days": found, "total": sum(d["count"] for d in found)}


def next_day(day):
    """The ISO date after `day`, for the exclusive end of a day's range."""
    return (date.fromisoformat(day) + timedelta(days=1)).isoformat()


def ordering(sort):
    """ORM ordering for parsed sort keys, with empty values last in both directions so the order
    reads the same on every database (PostgreSQL and SQLite differ by default)."""
    out = []
    for item in sort:
        column = item.lstrip("-")
        out.append(
            F(column).desc(nulls_last=True)
            if item.startswith("-")
            else F(column).asc(nulls_last=True)
        )
    return out


def parse_columns(entity: Entity, raw):
    if not raw:
        return [f for f in entity.fields if f.default]
    chosen = []
    for name in (part.strip() for part in raw.split(",") if part.strip()):
        field = entity.field(name)
        if field is None:
            names = ", ".join(f.key for f in entity.fields)
            raise QueryError("", f"Unknown column {name!r}; use {names}.", root="columns")
        if field not in chosen:
            chosen.append(field)
    return chosen


def _plain(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, UuidValue):
        return str(value)
    if hasattr(value, "value") and not isinstance(value, (int, float, bool, str)):
        return str(value)
    return value


def _read(obj, field):
    if field.read is not None:
        return _plain(field.read(obj))
    value = obj
    for part in field.column.split("__"):
        value = getattr(value, part, None)
        if value is None:
            return None
    return _plain(value)


def run(entity: Entity, event, user, *, tree, sort, columns, limit, offset, search=()):
    queryset = entity.base(event, user)
    if search:
        queryset = queryset.filter(compile_search(entity, search))
    if tree:
        queryset = queryset.filter(compile_filter(entity, tree))
    queryset = queryset.order_by(*ordering(sort), "pk")
    total = queryset.count()
    page = queryset[offset : offset + limit]
    rows = [{"id": str(obj.public_id), **{f.key: _read(obj, f) for f in columns}} for obj in page]
    return {"total": total, "rows": rows}


def one(entity: Entity, event, user, public_id):
    """One row with every registered field, or None when this person may not see it (or there is
    none): the same base queryset as the list, so a record is never reachable by id alone."""
    obj = entity.base(event, user).filter(public_id=public_id).first()
    if obj is None:
        return None
    return {"id": str(obj.public_id), **{f.key: _read(obj, f) for f in entity.fields}}


def answer(
    entity: Entity,
    event,
    user,
    *,
    tree,
    order,
    columns,
    terms,
    group=None,
    subgroup=None,
    calendar=None,
    month=None,
    limit,
    offset,
):
    """The one response of the entity query for the parts already parsed: rows, buckets or days.
    The route and a saved view's run both end here, so they can never answer differently."""
    body = {
        "entity": entity.key,
        "limit": limit,
        "offset": offset,
        "filter": tree,
        "sort": order,
        "search": " ".join(terms),
        "columns": [f.key for f in columns],
        "rows": [],
    }
    if calendar is not None:
        placed = run_days(entity, event, user, tree=tree, search=terms, field=calendar, month=month)
        body.update(
            total=placed["total"], calendar=calendar.key, month=placed["month"], days=placed["days"]
        )
    elif group is not None:
        buckets = run_groups(
            entity, event, user, tree=tree, search=terms, group=group, subgroup=subgroup
        )
        body.update(total=buckets["total"], group=group.key, groups=buckets["groups"])
        body["truncated"] = buckets["truncated"]
        if subgroup:
            body["subgroup"] = subgroup.key
    else:
        result = run(
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
        body.update(total=result["total"], rows=result["rows"])
    return body
