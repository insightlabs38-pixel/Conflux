from django import template
from django.utils.safestring import mark_safe

from ..sanitize import sanitize_html as _sanitize_html

register = template.Library()


@register.filter(name="sanitize_html")
def sanitize_html(value):
    """Re-sanitize at render time (defense in depth on top of save-time
    cleaning in blocks.clean_config) before marking safe for `{{ }}`."""
    return mark_safe(_sanitize_html(value or ""))


@register.simple_tag
def event_theme(event):
    from ..models import Page
    from ..themes import resolved_theme

    settings = resolved_theme(Page.objects.filter(event=event).first() if event else None)
    settings["style"] = ";".join(f"{key}:{value}" for key, value in settings["variables"].items())
    return settings
