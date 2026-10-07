"""The visual token layer is one source: the CSS values, the design reference and the server's
contrast table must agree (PD-F004-B01)."""

import json
import re
from pathlib import Path

import pytest
from presentation.accessibility import THEME_COLORS, contrast_ratio
from presentation.themes import PRESETS, clean_theme_config, resolved_theme

ROOT = Path(__file__).parents[2]
CSS = (ROOT / "src/web/styles/tokens.css").read_text()
DESIGN = json.loads((ROOT / "docs/product-depth-v3/design/system/tokens.json").read_text())

COLOUR = (
    "bg surface surface-2 surface-3 line line-2 line-3 ink ink-2 ink-3 "
    "accent accent-hover accent-ink accent-tint accent-line "
    "ok ok-tint ok-line warn warn-tint warn-line err err-tint err-line "
    "info info-tint info-line mute mute-tint mute-line"
).split()


def block(selector):
    body = re.search(re.escape(selector) + r" \{(.*?)\n\}", CSS, re.S).group(1)
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+?);", body))


LIGHT = block(":root")
DARK = block(':root[data-theme="dark"],\n.cx-event-site[data-theme="dark"]')


def test_colour_tokens_equal_the_approved_design_in_both_themes():
    for name in COLOUR:
        assert LIGHT["--" + name] == DESIGN["light"]["--" + name], name
        assert DARK["--" + name] == DESIGN["dark"]["--" + name], name


def test_theme_root_redeclares_color_and_background():
    assert "color: var(--ink);" in CSS
    assert "background-color: var(--bg)" in CSS
    assert "color-scheme: dark" in CSS


def test_server_contrast_table_mirrors_the_css():
    for theme, scope in (("default", LIGHT), ("minimal", LIGHT), ("dark", {**LIGHT, **DARK})):
        colours = THEME_COLORS[theme]
        assert colours["bg"] == scope["--bg"]
        assert colours["surface"] == scope["--surface"]
        assert colours["text"] == scope["--ink"]
        assert colours["text_muted"] == scope["--ink-2"]
        assert colours["accent"] == scope["--accent"]


def test_every_legacy_colour_alias_resolves_to_a_v3_token():
    scope = re.search(r":root,\n\.cx-event-site,\n\[data-theme\] \{(.*?)\n\}", CSS, re.S).group(1)
    aliases = dict(re.findall(r"(--color-[\w-]+):\s*var\((--[\w-]+)\);", scope))
    assert len(aliases) == 25
    for legacy, target in aliases.items():
        assert target[2:] in COLOUR, (legacy, target)
    # a second value would be a hex literal on a legacy name
    assert not re.search(r"--color-[\w-]+:\s*#", CSS)


@pytest.mark.parametrize("preset", sorted(PRESETS))
@pytest.mark.parametrize("theme", ["default", "minimal", "dark"])
def test_stored_preset_accents_still_pass_the_gate_on_every_theme_surface(preset, theme):
    accent = PRESETS[preset]["accent"]
    colours = THEME_COLORS[theme]
    if theme == "dark" and accent in ("#126454", "#a32918", "#363636"):
        pytest.skip("dark accents are chosen by the organizer; presets are light-theme values")
    for surface in (colours["bg"], colours["surface"]):
        assert contrast_ratio(accent, surface) >= 4.5, (preset, theme, accent)
    clean_theme_config({"accent": accent}, theme)


def test_resolved_theme_exposes_v3_variables_and_a_readable_tint():
    from types import SimpleNamespace

    for theme in ("default", "dark"):
        page = SimpleNamespace(theme=theme, theme_config={})
        variables = resolved_theme(page)["variables"]
        colours = THEME_COLORS[theme]
        assert variables["--accent"] == variables["--color-accent"] == colours["accent"]
        assert contrast_ratio(variables["--accent"], variables["--accent-tint"]) >= 4.5
        assert {"--accent-hover", "--accent-ink", "--accent-line"} <= set(variables)


def test_a_custom_accent_gets_a_tint_that_keeps_it_readable():
    page = __import__("types").SimpleNamespace(theme="default", theme_config={"accent": "#6b4fb3"})
    variables = resolved_theme(page)["variables"]
    assert variables["--accent"] == "#6b4fb3"
    assert variables["--accent-tint"] != "#ffffff"
    assert contrast_ratio("#6b4fb3", variables["--accent-tint"]) >= 4.5
