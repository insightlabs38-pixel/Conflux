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
