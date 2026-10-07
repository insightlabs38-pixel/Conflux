"""An organizer's preview of the public page with an appearance that is not saved yet
(PREVIEW_CONTEXT surface `page`, PD-F004-B03-T07).

The page is rendered by the same template and context a visitor gets (`site_views.landing_context`)
from the saved blocks, with the appearance from the request's `input` in place of the stored one.
The input is the draft appearance, data like any other preview input: the server validates it with
`themes.clean_theme_config` (the same rule as saving), stores nothing, and the caller's own
authorization applies (the endpoint is organizer and admin only, and the event must belong to the
workspace). The answer is the page as HTML for a sandboxed frame without scripts; what viewport it
is shown at is the browser's business.
"""

import re

from core import preview_context
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.template.loader import render_to_string
from events.models import Event

from .models import Page, PageTheme
from .site_views import landing_context
from .themes import ENUMS, FOCUS_KEYS, URL_KEYS, clean_theme_config

APPEARANCE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "theme": {"type": "string", "enum": list(PageTheme.values)},
        "theme_config": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                **{key: {"type": "string", "enum": list(values)} for key, values in ENUMS.items()},
                **{key: {"type": "string", "maxLength": 2048} for key in sorted(URL_KEYS)},
                **{
                    key: {"type": "integer", "minimum": 0, "maximum": 100}
                    for key in sorted(FOCUS_KEYS)
                },
                "accent": {"type": "string", "maxLength": 7},
            },
        },
    },
}


def _request(event) -> HttpRequest:
    request = HttpRequest()
    request.method = "GET"
    request.path = f"/e/{event.public_id}/"
    request.META["SERVER_NAME"] = "preview.invalid"
    request.META["SERVER_PORT"] = "80"
    return request


def resolve(user, workspace, ref, resolved, values):
    event = Event.objects.filter(workspace=workspace, public_id=ref["event"]).first()
    if event is None:
        return None
    saved = Page.objects.filter(event=event).first()
    theme = values.get("theme") or (saved.theme if saved else PageTheme.DEFAULT)
    config = (
        values["theme_config"]
        if "theme_config" in values
        else (saved.theme_config if saved else {})
    )
    try:
        config = clean_theme_config(config, theme)
    except ValidationError as error:
        raise preview_context.PreviewError({"input.theme_config": error.messages}) from error
    draft = Page(event=event, theme=theme, theme_config=config)  # never saved
    context = {**landing_context(event, saved), "theme": theme, "preview_page": draft}
    html = render_to_string("presentation/event_landing.html", context, request=_request(event))
    # The frame that shows it forbids scripts too: the offline-shell registration has no place in a
    # preview, so it is not sent, and a visitor's browser runs scripts, so the fallback for those
    # that do not (the language form's Go button) is left out rather than drawn.
    html = re.sub(r"<(script|noscript)\b.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    return {"html": html, "theme": theme, "theme_config": config}


def register():
    preview_context.register_surface(
        preview_context.Surface(
            key="page",
            label="Public page",
            params=("event",),
            resolve=resolve,
            input_schema=APPEARANCE,
        )
    )
