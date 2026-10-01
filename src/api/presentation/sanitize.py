"""Allowlist HTML sanitizer for organizer-authored rich text (PAGE-003).

The implementation is the `page` profile of the shared rich-content primitive (`core.rich`);
this module keeps the names the presentation app and its templates have always imported.
"""

from core.rich_page import (  # noqa: F401
    ALLOWED_ATTRS,
    ALLOWED_TAGS,
    SAFE_URL_SCHEMES,
    VOID_TAGS,
    sanitize_html,
)
