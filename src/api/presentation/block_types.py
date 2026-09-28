from copy import deepcopy

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


def item_schema(fields):
    return {
        "type": "array",
        "title": "Items",
        "maxItems": 20,
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


def normalize_config(schema, value, path="config"):
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict):
            raise ValidationError({path: "Must be an object."})
        properties = schema["properties"]
        if not schema["additionalProperties"] and value.keys() - properties.keys():
            raise ValidationError({path: "Unknown fields."})
        return {
            key: normalize_config(field, value.get(key, deepcopy(field["default"])), key)
            for key, field in properties.items()
        }
    if kind == "string":
        if not isinstance(value, str):
            raise ValidationError({path: "Must be text."})
        if schema.get("x-nonblank") and not value.strip():
            raise ValidationError({path: "This field is required."})
        if len(value) > schema["maxLength"]:
            raise ValidationError({path: f"Must be at most {schema['maxLength']} characters."})
        return value
    if kind == "integer":
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not schema["minimum"] <= value <= schema["maximum"]
        ):
            raise ValidationError(
                {path: f"Must be an integer from {schema['minimum']} to {schema['maximum']}."}
            )
        return value
    if kind == "array":
        if not isinstance(value, list) or len(value) > schema["maxItems"]:
            raise ValidationError({path: f"Must be a list of at most {schema['maxItems']} items."})
        return [normalize_config(schema["items"], item, path) for item in value]
    raise ValidationError({path: "Unsupported configuration type."})
