import re

from core.schema_subset import SchemaError
from core.schema_subset import normalize as normalize_schema
from django.core.exceptions import ValidationError


def text(title, maximum, *, required=False, widget="input", create_default=None):
    return {
        "type": "string",
        "title": title,
        "maxLength": maximum,
        "default": "",
        "x-nonblank": required,
        "x-widget": widget,
        "x-create-default": create_default,
    }


def object_schema(properties, *, strict=False):
    return {"type": "object", "properties": properties, "additionalProperties": not strict}


def item_schema(fields, *, maximum=20, title="Items"):
    return {
        "type": "array",
        "title": title,
        "maxItems": maximum,
        "default": [],
        "items": object_schema({name: text(name, 500) for name in fields}, strict=True),
    }


BLOCK_TYPES = {
    "hero": {
        "title": "Hero",
        "schema": object_schema(
            {
                "title": text("Title", 200, required=True, create_default="New hero"),
                "subtitle": text("Subtitle", 400),
                "cta_label": text("CTA label", 60),
                "cta_href": text("CTA link", 2000),
            }
        ),
    },
    # An event-specific lead (PD-F004-B03-T05): replaces the default hero for an event that has
    # something more useful to open with than a banner (a deadline, what to bring, who it is
    # for). One h1, a short body, up to four label/value facts and one action; no art, so it
    # never pushes the content down.
    "lead": {
        "title": "Lead (replaces the hero)",
        "schema": object_schema(
            {
                "title": text("Title", 200, required=True, create_default="Start here"),
                "body": text("Body", 600, widget="textarea"),
                "facts": item_schema(["label", "value"], maximum=4, title="Key facts"),
                "cta_label": text("Action label", 60),
                "cta_href": text("Action link", 2000),
            }
        ),
    },
    "cta": {
        "title": "Call to action",
        "schema": object_schema(
            {
                "label": text("Label", 60, required=True, create_default="Learn more"),
                "href": text("Link", 2000, required=True, create_default="/"),
            }
        ),
    },
    "rich_text": {
        "title": "Rich text",
        "schema": object_schema(
            {
                "html": text(
                    "HTML (sanitized on save)",
                    20000,
                    required=True,
                    widget="textarea",
                    create_default="<p>New content</p>",
                ),
            }
        ),
    },
    "faq": {
        "title": "FAQ",
        "schema": object_schema({"items": item_schema(["question", "answer"])}),
    },
    "sponsors": {
        "title": "Sponsors",
        "schema": object_schema({"items": item_schema(["name", "url"])}),
    },
    "resources": {
        "title": "Resources",
        "schema": object_schema({"items": item_schema(["label", "url"])}),
    },
    "gallery": {
        "title": "Gallery preview (live)",
        "schema": object_schema(
            {
                "limit": {
                    "type": "integer",
                    "title": "Projects to preview",
                    "minimum": 1,
                    "maximum": 24,
                    "default": 6,
                },
            }
        ),
    },
    **{
        kind: {"title": title, "schema": object_schema({}, strict=True)}
        for kind, title in [
            ("tracks", "Tracks (live)"),
            ("prizes", "Prizes (live)"),
            ("schedule", "Schedule (live)"),
            ("results", "Results (live)"),
            ("announcements", "Announcements (live)"),
        ]
    },
}


def _leaf(path, fallback):
    """The property a problem belongs to: `items[2].label` is `label`, a row is its array."""
    leaf = re.sub(r"\[\d+\]", "", path).rsplit(".", 1)[-1]
    return leaf or fallback


def normalize_config(schema, value, path="config"):
    """Validate and normalise block configuration with the platform schema subset
    (core.schema_subset, PD-F002-B02-T01). The first problem is reported under its property name,
    the same keys and messages as before the validator was shared."""
    try:
        return normalize_schema(schema, value)
    except SchemaError as exc:
        problem = exc.problems[0]
        raise ValidationError({_leaf(problem.path, path): problem.message}) from exc
