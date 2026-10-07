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
        ".cx-brand-mark",
        '.cx-queue-filters button[aria-pressed="true"]',
        '.cx-steps li[data-state="done"] .cx-steps__mark',
        ".cx-meter",
        ".cx-button--danger:hover:not(:disabled)",
        ".cx-shell a.cx-skip-link",
    },
    "styles/presentation.css": {".cx-hero__identity"},
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


# Decorative glyphs of the public hero and project cover (a letter or monogram, not text). The hero
# redesign (PD-F004-B02/B03) replaces them; until then they are the only literal sizes.
GLYPH_SIZES = {
    "styles/presentation.css": {
        ".cx-hero__identity span",
        '.cx-event-site[data-hero="poster"] .cx-hero__identity span',
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
        for value in re.findall(prop + r":\s*([^;]+);", match.group(2)):
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
