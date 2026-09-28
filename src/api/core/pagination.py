"""Bounded limit/offset paging for public list endpoints whose body is a bare
JSON array (kept for checker/SDK/embed compatibility). Paging metadata travels
in headers so the array shape does not change:

    X-Total-Count: total rows matching the filters
    Link: <...>; rel="next" / rel="prev"

Parameter rules match the portfolio endpoints: `limit` in 1..max, `offset` >= 0,
anything else is a 400.
"""

from urllib.parse import urlencode

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

DEFAULT_LIMIT = 50
MAX_LIMIT = 100
MAX_OFFSET = 10**7


def _int(request, name, default, low, high):
    raw = request.query_params.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError({name: "Must be an integer."}) from exc
    if not low <= value <= high:
        raise ValidationError({name: f"Must be between {low} and {high}."})
    return value


def page_params(request, *, default=DEFAULT_LIMIT, maximum=MAX_LIMIT):
    return _int(request, "limit", default, 1, maximum), _int(request, "offset", 0, 0, MAX_OFFSET)


def paged_response(request, queryset, rows_fn, *, limit, offset):
    """`rows_fn(sliced_queryset)` serialises one page; the count query is the
    only extra query, so cost is O(page) regardless of gallery size."""
    total = queryset.count()
    response = Response(rows_fn(queryset[offset : offset + limit]))
    response["X-Total-Count"] = str(total)
    base = request.build_absolute_uri(request.path)
    params = {k: v for k, v in request.query_params.items() if k not in ("limit", "offset")}

    def link(rel, new_offset):
        query = urlencode({**params, "limit": limit, "offset": new_offset})
        return f'<{base}?{query}>; rel="{rel}"'

    links = []
    if offset + limit < total:
        links.append(link("next", offset + limit))
    if offset > 0:
        links.append(link("prev", max(offset - limit, 0)))
    if links:
        response["Link"] = ", ".join(links)
    return response
