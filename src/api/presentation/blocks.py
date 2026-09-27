"""PageBlock kinds, their config schemas, and validation (PAGE-001/PAGE-002).

Each kind's config is a small JSON shape an organizer edits through the page
builder. "Live" kinds (TRACKS, PRIZES, SCHEDULE, GALLERY, RESULTS) take no
organizer content at all: they render the event's real domain data, so
there's nothing here for a rewrite of that data to go stale against.
"""

from django.core.exceptions import ValidationError

from .sanitize import sanitize_html

LIVE_KINDS = {"tracks", "prizes", "schedule", "gallery", "results"}


def _require_str(config, key, *, max_length, required=True):
    value = config.get(key, "")
    if not isinstance(value, str):
        raise ValidationError({key: "Must be text."})
    if required and not value.strip():
        raise ValidationError({key: "This field is required."})
    if len(value) > max_length:
        raise ValidationError({key: f"Must be at most {max_length} characters."})
    return value


def _require_items(config, *, fields, max_items=20):
    items = config.get("items", [])
    if not isinstance(items, list) or len(items) > max_items:
        raise ValidationError({"items": f"Must be a list of at most {max_items} items."})
    cleaned = []
    for item in items:
        if not isinstance(item, dict) or set(item) - set(fields):
            raise ValidationError({"items": f"Each item may only have: {', '.join(fields)}."})
        row = {}
        for field in fields:
            value = item.get(field, "")
            if not isinstance(value, str) or len(value) > 500:
                raise ValidationError({"items": f"'{field}' must be text under 500 characters."})
            row[field] = value
        cleaned.append(row)
    return cleaned


def clean_config(kind: str, config: dict) -> dict:
    """Validate + normalize `config` for `kind`. Raises ValidationError."""
    if not isinstance(config, dict):
        raise ValidationError("Block config must be an object.")

    if kind == "hero":
        return {
            "title": _require_str(config, "title", max_length=200),
            "subtitle": _require_str(config, "subtitle", max_length=400, required=False),
            "cta_label": _require_str(config, "cta_label", max_length=60, required=False),
            "cta_href": _require_str(config, "cta_href", max_length=2000, required=False),
        }
    if kind == "cta":
        return {
            "label": _require_str(config, "label", max_length=60),
            "href": _require_str(config, "href", max_length=2000),
        }
    if kind == "rich_text":
        raw = _require_str(config, "html", max_length=20000)
        return {"html": sanitize_html(raw)}
    if kind == "faq":
        return {"items": _require_items(config, fields=("question", "answer"))}
    if kind == "sponsors":
        return {"items": _require_items(config, fields=("name", "url"))}
    if kind == "resources":
        return {"items": _require_items(config, fields=("label", "url"))}
    if kind in LIVE_KINDS:
        if kind == "gallery":
            limit = config.get("limit", 6)
            if not isinstance(limit, int) or isinstance(limit, bool) or not (1 <= limit <= 24):
                raise ValidationError({"limit": "Must be an integer from 1 to 24."})
            return {"limit": limit}
        if config not in ({}, None):
            raise ValidationError("This block has no configuration.")
        return {}
    raise ValidationError({"kind": "Unknown block kind."})
