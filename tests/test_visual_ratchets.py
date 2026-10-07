"""Anti-slop ratchets over the web styles (V-COLOR, V-SLOP in the design contract): each rule
may only get stricter. A new use needs a written exception, i.e. an edit to the allowlist here."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src/web"
SHEETS = [*sorted((WEB / "styles").glob("*.css")), *sorted((WEB / "features").glob("*/*.css"))]

# Selectors allowed a solid saturated fill: actions and state markers, never structure.
SOLID_FILL_ALLOWED = {
    "styles/components.css": {
        ".cx-skip-link",
        ".cx-shell a.cx-skip-link:visited",
        ".cx-button--primary",
        '.cx-timeline [data-status="current"] .cx-timeline__marker',
        '.cx-queue-filters button[aria-pressed="true"]',
        '.cx-steps li[data-state="done"] .cx-steps__mark',
        ".cx-meter",
        ".cx-button--danger",
        ".cx-shell a.cx-skip-link",
    },
}
SOLID = re.compile(
    r"background(?:-color)?:\s*var\(--(?:color-)?(?:accent|success|warning|danger|info|ok|warn|err)\)"
)


def rules(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        yield " ".join(match.group(1).split()), match.group(2)


def test_no_gradients_anywhere():
    for sheet in SHEETS:
        assert "gradient" not in sheet.read_text(), sheet.name


def test_colour_literals_live_only_in_the_token_file():
    for sheet in SHEETS:
        if sheet.name == "tokens.css":
            continue
        text = re.sub(r"/\*.*?\*/", "", sheet.read_text(), flags=re.S)
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", text), sheet.name


def test_solid_saturated_fills_stay_on_actions_and_state_markers():
    for sheet in SHEETS:
        rel = str(sheet.relative_to(WEB))
        allowed = SOLID_FILL_ALLOWED.get(rel, set())
        found = {sel for sel, body in rules(sheet.read_text()) if SOLID.search(body)}
        # selector lists are compared member by member
        members = {part.strip() for sel in found for part in sel.split(",")}
        assert members <= allowed, (rel, sorted(members - allowed))


def test_ratchet_names_a_new_decorative_fill():
    sample = ".cx-card--promo { background: var(--color-accent); }"
    assert [sel for sel, body in rules(sample) if SOLID.search(body)] == [".cx-card--promo"]


# Decorative glyphs of the project cover (a letter or monogram, not text). The cover redesign
# (PD-F004-B03) replaces them; until then they are the only literal sizes.
GLYPH_SIZES = {
    "styles/presentation.css": {
        ".cx-project-cover",
        ".cx-project-card__cover, .cx-project-cover",
    },
}
FONT_SIZE = re.compile(r"font-size:\s*([^;]+);")
SCALE = re.compile(r"var\(--fs-(11|12|13|14|16|20|24|32|display)\)")


def declarations(text, prop):
    """Yield (selector, value) for `prop` in every rule, including rules inside @media."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        selector = " ".join(match.group(1).split()).split("}")[-1].strip()
        for value in re.findall(r"(?<![\w-])" + prop + r":\s*([^;]+);", match.group(2)):
            yield selector, value.strip()


def test_every_font_size_comes_from_the_type_scale():
    for sheet in SHEETS:
        if sheet.name == "tokens.css":
            continue
        rel = str(sheet.relative_to(WEB))
        for selector, value in declarations(sheet.read_text(), "font-size"):
            if selector in GLYPH_SIZES.get(rel, set()):
                continue
            assert SCALE.fullmatch(value) or value in ("inherit", "100%", "1em"), (
                rel,
                selector,
                value,
            )


def test_legacy_font_size_names_are_gone_and_weights_stay_on_plex_steps():
    for sheet in SHEETS:
        text = sheet.read_text()
        assert "--font-size-" not in text, sheet.name
        for _, value in declarations(text, "font-weight"):
            assert value in (
                "var(--font-weight-normal)",
                "var(--font-weight-medium)",
                "var(--font-weight-semibold)",
                "var(--font-weight-bold)",
                "inherit",
                "500",
                "600",
            ), (sheet.name, value)


def test_application_headings_stay_at_or_below_20px():
    text = (WEB / "styles/components.css").read_text()
    sizes = dict(
        (sel, val)
        for sel, val in declarations(text, "font-size")
        if sel.startswith(".cx-shell :where(h")
    )
    assert sizes == {
        ".cx-shell :where(h1)": "var(--fs-20)",
        ".cx-shell :where(h2)": "var(--fs-16)",
        ".cx-shell :where(h3)": "var(--fs-14)",
    }


SPACING = re.compile(r"^(padding|margin|gap|row-gap|column-gap)(-[a-z]+)?$")
# Scroll room under a sticky action bar; a size, not rhythm.
SPACING_LITERALS = {("styles/components.css", "padding-bottom", "10rem")}


def spacing_declarations(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        for prop, value in re.findall(r"([a-z-]+):\s*([^;]+);", match.group(2)):
            if SPACING.match(prop):
                yield prop, value.strip()


def test_spacing_comes_from_the_4px_scale_or_is_an_optical_nudge_of_two_pixels_or_less():
    for sheet in SHEETS:
        if sheet.name == "tokens.css":
            continue
        rel = str(sheet.relative_to(WEB))
        for prop, value in spacing_declarations(sheet.read_text()):
            if (rel, prop, value) in SPACING_LITERALS:
                continue
            stripped = re.sub(r"var\(--sp-\d+\)|calc\([^)]*\)|clamp\([^)]*\)", "", value)
            for number in re.findall(r"-?\d*\.?\d+(?:px|rem|em)", stripped):
                assert abs(float(re.match(r"-?[\d.]+", number).group())) <= 2 and number.endswith(
                    "px"
                ), (rel, prop, value)
            assert "--space-" not in value, (rel, prop, value)


def test_a_literal_rem_gap_is_named_by_the_spacing_ratchet():
    bad = list(spacing_declarations(".x { gap: 1rem; padding: 0 var(--sp-2); margin: -1px; }"))
    assert [v for _, v in bad if "rem" in v] == ["1rem"]


RADIUS_PART = re.compile(r"var\(--r-(?:1|2|3|pill)\)|0|inherit")


def test_radii_come_from_the_three_step_scale():
    for sheet in SHEETS:
        if sheet.name == "tokens.css":
            continue
        for selector, value in declarations(sheet.read_text(), "border-radius"):
            parts = re.findall(r"var\([^)]*\)|\S+", value)
            assert parts and all(RADIUS_PART.fullmatch(p) for p in parts), (
                sheet.name,
                selector,
                value,
            )
        assert "--radius-" not in sheet.read_text(), sheet.name


def test_no_status_label_is_a_pill():
    text = (WEB / "styles/components.css").read_text()
    assert dict(declarations(text, "border-radius"))[".cx-tag"] == "var(--r-1)"


# Shadows belong to floating layers only (V-ELEV-1); the rest is hairlines and spacing.
SHADOW_ALLOWED = {
    "styles/components.css": {
        ".cx-account__panel": "var(--sh-pop)",
        ".cx-consequence": "var(--sh-dlg)",
    },
}


def test_shadows_exist_only_on_floating_layers_with_the_elevation_tokens():
    for sheet in SHEETS:
        rel = str(sheet.relative_to(WEB))
        for selector, value in declarations(sheet.read_text(), "box-shadow"):
            if value == "none":
                continue
            assert SHADOW_ALLOWED.get(rel, {}).get(selector) == value, (rel, selector, value)
        assert "--shadow-" not in sheet.read_text(), rel


def test_overlays_use_the_scrim_and_floating_background_tokens():
    text = (WEB / "styles/components.css").read_text()
    assert dict(declarations(text, "background"))[".cx-consequence__backdrop"] == "var(--scrim)"
    assert dict(declarations(text, "background"))[".cx-consequence"] == "var(--float-bg)"
    assert dict(declarations(text, "background"))[".cx-account__panel"] == "var(--float-bg)"


def web_sources():
    for path in sorted(WEB.rglob("*.tsx")):
        parts = path.relative_to(WEB).parts
        if parts[0] in ("node_modules", "dist"):
            continue
        yield path


def test_icons_come_from_the_one_component_not_inline_svg():
    for path in web_sources():
        if path.name in ("Icon.tsx", "Icon.test.tsx") or ".test." in path.name:
            continue
        assert "<svg" not in path.read_text(), str(path.relative_to(WEB))


def test_icons_never_sit_on_coloured_tiles():
    for sheet in SHEETS:
        for selector, body in rules(sheet.read_text()):
            if "icon" in selector.lower() and "mark" not in selector.lower():
                assert not re.search(
                    r"background(-color)?:\s*var\(--(?:color-)?(?!surface|bg)", body
                ), (
                    sheet.name,
                    selector,
                )


def test_decorative_glyph_characters_are_not_used_as_icons_in_css_content():
    for sheet in SHEETS:
        for _, value in declarations(sheet.read_text(), "content"):
            assert (
                value in ('"/"', '"− "', '"+ "', '"Account"', '""', "none") or "attr(" in value
            ), (
                sheet.name,
                value,
            )


def test_the_colour_chip_badge_is_gone_for_status_and_tag():
    for sheet in SHEETS:
        assert "cx-badge" not in sheet.read_text(), sheet.name
    for path in web_sources():
        if path.name == "Status.test.tsx":
            continue
        text = path.read_text()
        assert "cx-badge" not in text, str(path.relative_to(WEB))
        assert "components/Badge" not in text and './Badge"' not in text, str(path.relative_to(WEB))


def test_status_is_an_icon_and_a_word_and_never_a_fill():
    text = (WEB / "styles/components.css").read_text()
    for selector, body in rules(text):
        if selector.startswith(".cx-status"):
            assert "background" not in body, selector
    assert (WEB / "components/Status.tsx").read_text().count("<Icon") == 1


TRANSITION_PROPERTIES = {"background-color", "border-color", "color"}
# State indicators that animate while work is pending; each needs a reduced-motion fallback.
ANIMATIONS_ALLOWED: set[str] = {"cx-spin"}


def test_motion_is_a_short_state_transition_and_nothing_is_ambient():
    for sheet in SHEETS:
        text = sheet.read_text()
        assert "--motion-" not in text, sheet.name
        for selector, value in declarations(text, "transition"):
            if value == "none":
                continue
            assert "all" not in value.split(), (sheet.name, selector, value)
            parts = [p.strip() for p in value.split(",")]
            for part in parts:
                prop = part.split()[0]
                assert prop in TRANSITION_PROPERTIES, (sheet.name, selector, part)
                assert "var(--t-fast)" in part or "var(--t-base)" in part, (
                    sheet.name,
                    selector,
                    part,
                )
        for name in re.findall(r"@keyframes\s+([\w-]+)", text):
            assert name in ANIMATIONS_ALLOWED, (sheet.name, name)
        for selector, value in declarations(text, "animation"):
            assert value == "none" or value.split()[0] in ANIMATIONS_ALLOWED, (
                sheet.name,
                selector,
                value,
            )


def test_reduced_motion_overrides_every_component():
    text = (WEB / "styles/components.css").read_text()
    block = re.search(r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", text, re.S).group(1)
    for needle in (
        "transition-duration: 0.01ms !important",
        "animation-duration: 0.01ms !important",
    ):
        assert needle in block
    assert "scroll-behavior: auto !important" in block


def test_every_empty_state_says_why_and_none_is_a_bare_headline():
    for path in web_sources():
        text = path.read_text()
        if path.name in ("EmptyState.tsx",) or ".test." in path.name:
            continue
        for match in re.finditer(r"<EmptyState\b(.*?)(?:/>|>)", text, re.S):
            opening = match.group(1)
            assert re.search(r"\bwhy=", opening), (str(path.relative_to(WEB)), opening[:80])


# Not a plain failed load: the error boundary renders a crash, and the config history panel merges
# its load and restore errors into one message.
ERROR_STATE_EXEMPT = {"features/pvs/Guarded.tsx", "features/audit/ConfigHistoryPanel.tsx"}


def test_every_error_state_with_a_retry_says_what_failed_and_what_retry_does():
    for path in web_sources():
        rel = str(path.relative_to(WEB))
        if ".test." in path.name or rel in ERROR_STATE_EXEMPT or path.name == "ErrorState.tsx":
            continue
        for match in re.finditer(r"<ErrorState\b(.*?)/>", path.read_text(), re.S):
            opening = match.group(1)
            if "onRetry" in opening:
                assert re.search(r'kind="read"|\bkept=', opening), (rel, opening[:90])


def test_no_dashed_or_dotted_borders_and_every_disclosure_has_the_one_chevron():
    for sheet in SHEETS:
        text = sheet.read_text()
        assert "dashed" not in text and "dotted" not in text, sheet.name
    text = (WEB / "styles/components.css").read_text()
    block = dict(rules(text))
    assert block[".cx-shell__main details > summary::before"].count("border-right") == 1
    assert "list-style: none" in block[".cx-shell__main details > summary"]


def test_a_scroll_region_contains_its_absolutely_positioned_cells():
    # a visually-hidden header (position: absolute) inside a static scroll region escaped its clip
    # and made the whole page scroll sideways at 390px (organizer eligibility queue)
    block = dict(rules((WEB / "styles/components.css").read_text()))
    assert "position: relative" in block[".cx-scroll-region"]


def test_no_browser_spec_selects_the_removed_badge_class():
    # a spec that waits for `.cx-badge` times out forever once Badge is gone (lifecycle and pvs did)
    for spec in sorted((ROOT / "tests/e2e").glob("*.spec.ts")):
        if spec.name == "visual-foundation.spec.ts":  # asserts the class is absent
            continue
        assert "cx-badge" not in spec.read_text(), spec.name


def test_server_rendered_pages_do_not_use_the_removed_badge_class():
    # the public templates kept `cx-badge` after the React Badge went, so statuses rendered as bare text
    for template in sorted((ROOT / "src/api").glob("**/templates/**/*.html")):
        assert "cx-badge" not in template.read_text(), str(template.relative_to(ROOT))
