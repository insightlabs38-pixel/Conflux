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


def px(value):
    value = value.strip()
    return float(value[:-3]) * 16 if value.endswith("rem") else float(value[:-2])


def test_type_scale_equals_the_design_in_px():
    scale = {int(k[5:]): px(v) for k, v in LIGHT.items() if re.fullmatch(r"--fs-\d+", k)}
    assert sorted(scale) == DESIGN["type_scale_px"]
    assert all(scale[size] == size for size in scale)
    for name in ("lh-tight", "lh-ui", "lh-read"):
        assert LIGHT["--" + name] == DESIGN["light"]["--" + name]
    for name in ("font-sans", "font-mono", "font-read"):
        assert LIGHT["--" + name].split(",")[0] == DESIGN["light"]["--" + name].split(",")[0]
    assert "system-ui" in LIGHT["--font-sans"], "public pages assert a system fallback"


def test_display_size_stays_inside_the_scale():
    assert LIGHT["--fs-display"] == "clamp(var(--fs-24), 4vw, var(--fs-32))"


def test_spacing_and_height_tokens_equal_the_design_in_px():
    for name in (1, 2, 3, 4, 5, 6, 8, 10, 12):
        assert px(LIGHT[f"--sp-{name}"]) == px(DESIGN["light"][f"--sp-{name}"]), name
    for name in ("h-ctl", "h-ctl-sm", "h-ctl-lg", "h-row", "h-row-dense", "h-row-comfy", "h-top"):
        assert px(LIGHT["--" + name]) == px(DESIGN["light"]["--" + name]), name
    assert px(LIGHT["--h-touch"]) == 44 == px(DESIGN["light"]["--h-touch"])


def test_touch_layouts_raise_every_control_height_to_the_touch_target():
    match = re.search(
        r"@media \(max-width: 47.9375rem\), \(pointer: coarse\) \{\s*:root \{(.*?)\}", CSS, re.S
    )
    assert match, "touch override missing"
    raised = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", match.group(1)))
    assert raised == {
        "--h-ctl": "var(--h-touch)",
        "--h-ctl-sm": "var(--h-touch)",
        "--h-ctl-lg": "var(--h-touch)",
    }


def test_legacy_spacing_and_control_names_are_gone():
    assert not re.search(r"--space-\d|--control-height", CSS)


def test_radii_equal_the_design_and_legacy_radius_names_are_gone():
    for name in ("r-1", "r-2", "r-3", "r-pill"):
        assert LIGHT["--" + name] == DESIGN["light"]["--" + name], name
    assert not re.search(r"--radius-", CSS)


def norm(value):
    return re.sub(r"\s+", " ", value.replace(" .", " 0.").replace("(.", "(0.")).strip()


def test_elevation_tokens_equal_the_design_in_both_themes():
    for name in ("sh-pop", "sh-dlg"):
        assert norm(LIGHT["--" + name]) == norm(DESIGN["light"]["--" + name]), name
        assert norm(DARK["--" + name]) == norm(DESIGN["dark"]["--" + name]), name
    assert LIGHT["--float-bg"] == "var(--surface)"
    assert DARK["--float-bg"] == "var(--surface-2)"
    assert not re.search(r"--shadow-", CSS)


# The palette before PD-F004-B01 (bg, raised surface) per theme: a stored organizer accent that the
# gate accepted then must still be accepted now, so no stored theme_config becomes invalid.
OLD_SURFACES = {"light": ("#f4f6f5", "#ffffff"), "dark": ("#12161c", "#1b2028")}


def accepted(accent, surfaces):
    return all(contrast_ratio(accent, surface) >= 4.5 for surface in surfaces)


def test_every_accent_the_old_gate_accepted_is_still_accepted():
    steps = range(0, 256, 17)
    checked = 0
    for r in steps:
        for g in steps:
            for b in steps:
                accent = f"#{r:02x}{g:02x}{b:02x}"
                for old, theme in (("light", "default"), ("dark", "dark")):
                    if accepted(accent, OLD_SURFACES[old]):
                        checked += 1
                        new = THEME_COLORS[theme]
                        assert accepted(accent, (new["bg"], new["surface"])), (accent, theme)
    assert checked > 1000


def test_the_gate_still_refuses_a_low_contrast_accent_with_its_message():
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError) as caught:
        clean_theme_config({"accent": "#cccccc"}, "default")
    assert "4.5:1" in str(caught.value)


def test_motion_tokens_equal_the_design_and_legacy_names_are_gone():
    assert LIGHT["--t-fast"] == DESIGN["light"]["--t-fast"] == "120ms"
    assert LIGHT["--t-base"] == DESIGN["light"]["--t-base"] == "180ms"
    assert not re.search(r"--motion-", CSS)
