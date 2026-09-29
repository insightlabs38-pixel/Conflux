"""Static accessibility audit for an organizer's composed public page
(S22): contrast, heading structure, accessible link names, and keyboard
operability. Every rule here checks something a `Page`/`PageBlock` can
actually contain today -- it reports what a real WCAG audit would flag,
not a hypothetical redesign.
"""

import re

# Mirrors src/web/styles/tokens.css exactly. Kept here rather than parsed
# from the CSS at runtime -- there is no shared build step between the
# Django backend and the Vite frontend for design tokens, and inventing
# one is out of this batch's scope. THEME_COLORS must be updated by hand
# if tokens.css's palette changes.
THEME_COLORS = {
    "default": {
        "bg": "#f4f6f5",
        "text": "#16202b",
        "text_muted": "#56626d",
        "accent": "#126454",
    },
    "minimal": {
        # .theme-minimal only changes shadows/radius, not the palette.
        "bg": "#f4f6f5",
        "text": "#16202b",
        "text_muted": "#56626d",
        "accent": "#126454",
    },
    "dark": {
        "bg": "#12161c",
        "text": "#e8ecf1",
        "text_muted": "#a7b0bb",
        "accent": "#6d8fff",
    },
}

# WCAG 2.1 SC 1.4.3: 4.5:1 for normal text, 3:1 for large text/UI
# components. Body/muted text is checked at the stricter ratio; the accent
# color is checked at the looser one since it is typically used for
# larger or bolder call-to-action text, matching how it renders today.
AA_NORMAL_TEXT = 4.5
AA_LARGE_TEXT = 3.0

VAGUE_LINK_TEXT = {"click here", "here", "click", "link", "more", "read more", "learn more"}


def _srgb_channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    rl, gl, bl = _srgb_channel(r), _srgb_channel(g), _srgb_channel(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG relative-luminance contrast ratio between two hex colors,
    always >= 1.0 regardless of argument order.
    """
    la, lb = _relative_luminance(hex_a), _relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _warning(category, message, *, block=None):
    return {
        "category": category,
        "severity": "warning",
        "message": message,
        "block_public_id": str(block.public_id) if block is not None else None,
    }


def audit_theme(theme: str) -> list[dict]:
    """Contrast warnings for one of the three fixed themes."""
    colors = THEME_COLORS.get(theme, THEME_COLORS["default"])
    warnings = []
    text_ratio = contrast_ratio(colors["text"], colors["bg"])
    if text_ratio < AA_NORMAL_TEXT:
        warnings.append(
            _warning(
                "contrast",
                f"'{theme}' theme body text contrast is {text_ratio:.2f}:1, "
                f"below the WCAG AA minimum of {AA_NORMAL_TEXT}:1.",
            )
        )
    muted_ratio = contrast_ratio(colors["text_muted"], colors["bg"])
    if muted_ratio < AA_NORMAL_TEXT:
        warnings.append(
            _warning(
                "contrast",
                f"'{theme}' theme muted text contrast is {muted_ratio:.2f}:1, "
                f"below the WCAG AA minimum of {AA_NORMAL_TEXT}:1.",
            )
        )
    accent_ratio = contrast_ratio(colors["accent"], colors["bg"])
    if accent_ratio < AA_LARGE_TEXT:
        warnings.append(
            _warning(
                "contrast",
                f"'{theme}' theme accent (link/CTA) contrast is "
                f"{accent_ratio:.2f}:1, below the WCAG AA minimum of "
                f"{AA_LARGE_TEXT}:1 for large text and UI components.",
            )
        )
    return warnings


def _heading_warnings(block) -> list[dict]:
    levels = [int(level) for level in re.findall(r"<h([234])>", block.config.get("html", ""))]
    warnings = []
    if levels and levels[0] != 2:
        warnings.append(
            _warning(
                "heading",
                f"This section's first heading is h{levels[0]}; sections should "
                "open at h2 (the page title is the only h1).",
                block=block,
            )
        )
    for previous, current in zip(levels, levels[1:]):
        if current - previous > 1:
            warnings.append(
                _warning(
                    "heading",
                    f"Heading level jumps from h{previous} to h{current} without "
                    "an intervening heading.",
                    block=block,
                )
            )
    return warnings


def _accessible_name_warnings(block) -> list[dict]:
    warnings = []
    if block.kind == "hero":
        label = block.config.get("cta_label", "")
        if block.config.get("cta_href") and label.strip().lower() in VAGUE_LINK_TEXT:
            warnings.append(
                _warning(
                    "accessible-name",
                    f"Hero call-to-action text '{label}' doesn't describe its "
                    "destination on its own.",
                    block=block,
                )
            )
    elif block.kind == "cta":
        label = block.config.get("label", "")
        if label.strip().lower() in VAGUE_LINK_TEXT:
            warnings.append(
                _warning(
                    "accessible-name",
                    f"Call-to-action text '{label}' doesn't describe its destination on its own.",
                    block=block,
                )
            )
    elif block.kind in ("resources", "sponsors"):
        name_field = "label" if block.kind == "resources" else "name"
        for item in block.config.get("items", []):
            text = item.get(name_field, "")
            if text.strip().lower() in VAGUE_LINK_TEXT:
                warnings.append(
                    _warning(
                        "accessible-name",
                        f"A {block.kind[:-1]} link's text '{text}' doesn't "
                        "describe its destination on its own.",
                        block=block,
                    )
                )
    return warnings


def _keyboard_warnings(block) -> list[dict]:
    if block.kind != "rich_text":
        return []
    warnings = []
    if "<a>" in block.config.get("html", ""):
        warnings.append(
            _warning(
                "keyboard",
                "This section has a link with no destination -- it renders as "
                "text a keyboard user can't reach or activate.",
                block=block,
            )
        )
    return warnings


def audit_page(page) -> list[dict]:
    """Every accessibility warning for `page`: theme contrast plus a
    heading/accessible-name/keyboard pass over each of its blocks, in
    block order. Never blocks a save -- purely advisory, like the rest of
    this audit.
    """
    warnings = list(audit_theme(page.theme))
    hero_count = 0
    for block in page.blocks.all():
        if block.kind == "hero":
            hero_count += 1
            if hero_count > 1:
                warnings.append(
                    _warning(
                        "heading",
                        "More than one hero block on this page means more than "
                        "one h1 -- a page should have exactly one.",
                        block=block,
                    )
                )
        warnings.extend(_heading_warnings(block))
        warnings.extend(_accessible_name_warnings(block))
        warnings.extend(_keyboard_warnings(block))
    return warnings
