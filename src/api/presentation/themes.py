"""Constrained event presentation settings; never organizer-authored CSS or script."""

import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

from .accessibility import THEME_COLORS, contrast_ratio

ENUMS = {
    "typography": ("system", "editorial", "technical"),
    "personality": ("restrained", "expressive", "square"),
    "density": ("comfortable", "compact"),
    "width": ("standard", "wide"),
    "hero": ("split", "poster", "editorial"),
    "background": ("canvas", "paper"),
    "project_card": ("visual", "compact"),
}
DEFAULTS = {key: values[0] for key, values in ENUMS.items()}
PRESETS = {
    "technical": {
        "typography": "technical",
        "personality": "square",
        "hero": "split",
        "density": "compact",
        "width": "wide",
        "accent": "#126454",
    },
    "student": {
        "typography": "system",
        "personality": "expressive",
        "hero": "poster",
        "density": "comfortable",
        "width": "wide",
        "accent": "#a32918",
    },
    "conference": {
        "typography": "editorial",
        "personality": "restrained",
        "hero": "editorial",
        "density": "comfortable",
        "background": "paper",
        "accent": "#363636",
    },
}


def clean_theme_config(value, theme="default"):
    if not isinstance(value, dict) or set(value) - (
        set(ENUMS) | {"accent", "logo_url", "banner_url"}
    ):
        raise ValidationError(
            {"theme_config": "Use only supported brand and presentation settings."}
        )
    result = dict(value)
    for key, choices in ENUMS.items():
        if key in result and result[key] not in choices:
            raise ValidationError({"theme_config": f"Unsupported {key} preset."})
    for key in ("logo_url", "banner_url"):
        if key not in result:
            continue
        url = result[key]
        if not isinstance(url, str) or len(url) > 2048:
            raise ValidationError({"theme_config": f"Invalid {key}."})
        if not url:
            result.pop(key)
            continue
        try:
            parsed = urlsplit(url)
            valid = (
                parsed.scheme in ("http", "https")
                and parsed.hostname
                and parsed.username is None
                and parsed.password is None
            )
        except ValueError:
            valid = False
        if not valid or re.search(r'[\s\\<>"\x00-\x1f]', url):
            raise ValidationError(
                {"theme_config": f"{key} must be a safe absolute HTTP(S) image URL."}
            )
    if "accent" in result:
        accent = result["accent"]
        if not isinstance(accent, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            raise ValidationError({"theme_config": "Accent must be a six-digit hex color."})
        colors = THEME_COLORS.get(theme, THEME_COLORS["default"])
        surfaces = [colors["bg"], "#1b2028" if theme == "dark" else "#ffffff"]
        if min(contrast_ratio(accent, surface) for surface in surfaces) < 4.5:
            raise ValidationError(
                {"theme_config": "Accent needs at least 4.5:1 contrast on event surfaces."}
            )
        result["accent"] = accent.lower()
    return result


def resolved_theme(page):
    theme = page.theme if page else "default"
    config = clean_theme_config(page.theme_config if page else {}, theme)
    settings = {**DEFAULTS, **config, "mode": theme}
    if theme == "minimal" and "personality" not in config:
        settings["personality"] = "square"
    accent = config.get("accent", THEME_COLORS[theme]["accent"])
    ink = max(("#ffffff", "#0c1220"), key=lambda color: contrast_ratio(accent, color))
    # A fixed validated accent is used for all interaction states; state is also
    # conveyed by underline/border, never by an unvalidated color transformation.
    settings["accent"] = accent
    settings["variables"] = {
        "--color-accent": accent,
        "--color-accent-strong": accent,
        "--color-accent-active": accent,
        "--color-focus-ring": accent,
        "--color-accent-contrast": ink,
    }
    return settings
