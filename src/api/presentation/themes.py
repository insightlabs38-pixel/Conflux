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
    # How much room the public hero takes (PD-F004-B02-T08): compact is the default and what a theme
    # without the key means, so no stored theme needs a migration. `immersive` (PD-F004-B03-T01) is
    # the artwork-led opt-in and needs a hero image (checked in clean_theme_config).
    "hero_size": ("compact", "none", "standard", "immersive"),
    "background": ("canvas", "paper"),
    "project_card": ("visual", "compact"),
}
DEFAULTS = {key: values[0] for key, values in ENUMS.items()}
# Hero art direction (PD-F004-B03-T06): where the picture is cropped from, as a percentage from the
# left and the top (the CSS object-position), and an optional picture used instead on a phone.
FOCUS_KEYS = {"banner_focus_x", "banner_focus_y"}
URL_KEYS = {"logo_url", "banner_url", "banner_mobile_url"}
FOCUS_DEFAULT = 50
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
        set(ENUMS) | URL_KEYS | FOCUS_KEYS | {"accent"}
    ):
        raise ValidationError(
            {"theme_config": "Use only supported brand and presentation settings."}
        )
    result = dict(value)
    for key, choices in ENUMS.items():
        if key in result and result[key] not in choices:
            raise ValidationError({"theme_config": f"Unsupported {key} preset."})
    for key in sorted(FOCUS_KEYS & set(result)):
        number = result[key]
        if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number <= 100:
            raise ValidationError(
                {"theme_config": f"{key} is a whole number of percent from 0 to 100."}
            )
        if number == FOCUS_DEFAULT:
            result.pop(key)  # the centre is what no setting means
    for key in sorted(URL_KEYS & set(result)):
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
    if result.get("hero_size") == "immersive" and not result.get("banner_url"):
        raise ValidationError(
            {
                "theme_config": "The immersive hero is built around artwork: add a hero image URL "
                "first, or choose compact or standard."
            }
        )
    if result.get("banner_mobile_url") and not result.get("banner_url"):
        raise ValidationError(
            {
                "theme_config": "A phone image is an alternative to the hero image: "
                "add the hero image first."
            }
        )
    if "accent" in result:
        accent = result["accent"]
        if not isinstance(accent, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            raise ValidationError({"theme_config": "Accent must be a six-digit hex color."})
        colors = THEME_COLORS.get(theme, THEME_COLORS["default"])
        surfaces = [colors["bg"], colors["surface"]]
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
    colors = THEME_COLORS.get(theme, THEME_COLORS["default"])
    tint = _accent_tint(accent, colors["surface"])
    focus = {
        f"--hero-focus-{axis}": f"{config.get(f'banner_focus_{axis}', FOCUS_DEFAULT)}%"
        for axis in ("x", "y")
    }
    settings["variables"] = {
        **focus,
        # v3 names: what new CSS reads. The legacy --color-* names resolve from these in the
        # stylesheet; they are listed too so clients that already apply them keep working.
        "--accent": accent,
        "--accent-hover": accent,
        "--accent-ink": ink,
        "--accent-tint": tint,
        "--accent-line": accent,
        "--color-accent": accent,
        "--color-accent-strong": accent,
        "--color-accent-active": accent,
        "--color-focus-ring": accent,
        "--color-accent-contrast": ink,
    }
    return settings


def _mix(foreground, background, share):
    """sRGB mix of two #rrggbb colors; `share` is the foreground fraction."""
    fg = [int(foreground[i : i + 2], 16) for i in (1, 3, 5)]
    bg = [int(background[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(f * share + b * (1 - share)):02x}" for f, b in zip(fg, bg))


def _accent_tint(accent, surface):
    """Selected-row background for an organizer accent: the strongest tint on which the accent
    still reads at 4.5:1, so accent text on it stays accessible; the plain surface otherwise."""
    for share in (0.12, 0.08, 0.04):
        tint = _mix(accent, surface, share)
        if contrast_ratio(accent, tint) >= 4.5:
            return tint
    return surface
