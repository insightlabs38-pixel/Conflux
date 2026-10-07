import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

from .block_types import BLOCK_TYPES, normalize_config
from .sanitize import sanitize_html

LIVE_KINDS = {"tracks", "prizes", "schedule", "gallery", "results", "announcements"}

# Links an organizer types into a block. They are rendered on the public site, which shares an
# origin with the application, so a `javascript:` or `data:` link would run as the visitor: only
# a path on this site, an anchor, or an http(s) or mailto link is accepted at save time, and the
# template drops anything else again at render time (safe_href), so a value stored earlier
# cannot run either.
LINK_FIELDS = {
    "hero": ("cta_href",),
    "lead": ("cta_href",),
    "cta": ("href",),
}
LINK_ITEM_FIELDS = {"sponsors": "url", "resources": "url"}


def safe_href(value) -> str:
    """The link if it is relative to this site (a path, `gallery/`, an anchor), an http(s) or mailto
    link; else ''."""
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or re.search(r"[\s\\<>\"\x00-\x1f]", value):
        return ""
    if value.startswith("//"):
        return ""
    try:
        parts = urlsplit(value)
    except ValueError:
        return ""
    if not parts.scheme and not parts.netloc:  # a path, an anchor or a query: relative to this site
        return value
    if parts.scheme in ("http", "https") and parts.hostname:
        return value
    if parts.scheme == "mailto" and parts.path:
        return value
    return ""


def _check_links(kind, cleaned):
    message = "Use a path on this site, an anchor, or an http(s) or mailto link."
    for field in LINK_FIELDS.get(kind, ()):
        value = cleaned.get(field, "")
        if value and not safe_href(value):
            raise ValidationError({field: message})
    field = LINK_ITEM_FIELDS.get(kind)
    for item in cleaned.get("items", []) if field else []:
        if item.get(field) and not safe_href(item[field]):
            raise ValidationError({"items": f"A {field} link is not allowed. {message}"})


def clean_config(kind: str, config: dict) -> dict:
    definition = BLOCK_TYPES.get(kind)
    if definition is None:
        raise ValidationError({"kind": "Unknown kind."})
    cleaned = normalize_config(definition["schema"], config)
    if kind == "rich_text":
        cleaned["html"] = sanitize_html(cleaned["html"])
    _check_links(kind, cleaned)
    return cleaned
