from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import template
from django.utils import formats, timezone
from django.utils.safestring import mark_safe

from ..blocks import safe_href as _safe_href
from ..sanitize import sanitize_html as _sanitize_html
from ..showcase import initials as _initials

register = template.Library()


@register.filter(name="sanitize_html")
def sanitize_html(value):
    """Re-sanitize at render time (defense in depth on top of save-time
    cleaning in blocks.clean_config) before marking safe for `{{ }}`."""
    return mark_safe(_sanitize_html(value or ""))


@register.filter(name="initials")
def initials(value):
    """What a name is drawn as without artwork (showcase.initials, the one rule)."""
    return _initials(value)


@register.filter(name="safe_href")
def safe_href(value):
    """A link an organizer typed, or '' when it is not a path, anchor, http(s) or mailto link."""
    return _safe_href(value)


@register.simple_tag(takes_context=True)
def event_theme(context, event):
    from ..models import Page
    from ..themes import resolved_theme

    # An organizer's preview renders the page with an unsaved appearance (PREVIEW_CONTEXT surface
    # `page`); a visitor's request has none and reads the stored one.
    page = context.get("preview_page")
    if page is None:
        page = Page.objects.filter(event=event).first() if event else None
    settings = resolved_theme(page)
    settings["style"] = ";".join(f"{key}:{value}" for key, value in settings["variables"].items())
    return settings


@register.simple_tag
def event_facts(event):
    """The hero's status and dates as plain words, dates in the event's own timezone:
    "Open · Jan. 1, 2026 – Jan. 2, 2026 · UTC". Nothing is shown for a date that is not set."""
    parts = [event.get_status_display()]
    if event.starts_at and event.ends_at:
        try:
            zone = ZoneInfo(event.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            zone = ZoneInfo("UTC")
        start, end = (
            formats.date_format(timezone.localtime(value, zone), "N j, Y")
            for value in (event.starts_at, event.ends_at)
        )
        parts.append(start if start == end else f"{start} \u2013 {end}")
        parts.append(event.timezone)
    return " \u00b7 ".join(parts)
