from django.core.exceptions import ValidationError

from .block_types import BLOCK_TYPES, normalize_config
from .sanitize import sanitize_html

LIVE_KINDS = {"tracks", "prizes", "schedule", "gallery", "results", "announcements"}


def clean_config(kind: str, config: dict) -> dict:
    definition = BLOCK_TYPES.get(kind)
    if definition is None:
        raise ValidationError({"kind": "Unknown kind."})
    cleaned = normalize_config(definition["schema"], config)
    if kind == "rich_text":
        cleaned["html"] = sanitize_html(cleaned["html"])
    return cleaned
