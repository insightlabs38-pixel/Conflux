"""The committed Claude Design handoff is the design authority; its manifest must resolve."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs/product-depth-v3/design"
FOUNDATION = {
    "design/system-v3",
    "design/app-shell",
    "design/organizer-data-surface",
    "design/participant-my-event",
    "design/project-story-editor",
    "design/judge-review",
    "design/deliberation-awards",
    "design/public-event",
    "design/public-project",
    "design/event-builder",
    "design/onsite-mobile",
    "design/state-matrix",
}


def load(path=DESIGN / "DESIGN_MANIFEST.yaml"):
    return yaml.safe_load(path.read_text())


def missing_artifacts(manifest, base=DESIGN):
    gone = []
    for ref in manifest["references"]:
        for value in ref["artifacts"].values():
            for rel in [value] if isinstance(value, str) else value:
                if not (base / rel).is_file():
                    gone.append(f"{ref['id']}: {rel}")
    return gone


def test_every_foundation_reference_is_approved_and_unique():
    refs = load()["references"]
    ids = [r["id"] for r in refs]
    assert len(ids) == len(set(ids))
    assert FOUNDATION <= set(ids)
    assert {r["status"] for r in refs} == {"APPROVED"}
    assert load()["status"] == "FOUNDATION_FROZEN_FOR_IMPLEMENTATION"


def test_every_artifact_is_committed_locally():
    assert missing_artifacts(load()) == []


def test_each_reference_has_html_and_screenshots_at_a_desktop_and_a_state_viewport():
    for ref in load()["references"]:
        art = ref["artifacts"]
        assert art["readme"], ref["id"]
        assert art["html"] and art["screenshots"], ref["id"]
        assert ref["viewport_coverage"] and ref["state_coverage"], ref["id"]
        assert ref["must_preserve"], ref["id"]


def test_tokens_and_source_notes_exist():
    manifest = load()
    for key in ("tokens", "tokens_json", "component_mapping"):
        assert (DESIGN / manifest[key]).is_file(), key
    assert (DESIGN / "exports/r2.1/SOURCE.md").is_file()


def test_a_dangling_artifact_is_reported_with_its_reference(tmp_path):
    manifest = load()
    manifest["references"][0]["artifacts"]["html"] = ["system/prototypes/html/Nope.html"]
    assert missing_artifacts(manifest) == ["design/system-v3: system/prototypes/html/Nope.html"]


TOKENS_CSS = DESIGN / "system/tokens.css"
TOKENS_JSON = DESIGN / "system/tokens.json"


def parse_block(css, selector):
    body = css.split(selector + " {", 1)[1].split("\n}", 1)[0]
    return {k: v.strip() for k, v in re.findall(r"(--[\w-]+):\s*([^;]+?);", body)}


def luminance(hex_color):
    h = hex_color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def themes():
    css = TOKENS_CSS.read_text()
    light = parse_block(css, ":root")
    dark = {**light, **parse_block(css, '[data-theme="dark"]')}
    return light, dark


def test_tokens_css_and_json_do_not_drift():
    spec = json.loads(TOKENS_JSON.read_text())
    css = TOKENS_CSS.read_text()
    assert spec["revision"] == load()["design_revision"]
    assert parse_block(css, ":root") == spec["light"]
    assert parse_block(css, '[data-theme="dark"]') == spec["dark"]


def test_scales_match_the_contract():
    light, _ = themes()
    sizes = sorted(int(v[:-2]) for k, v in light.items() if k.startswith("--fs-"))
    assert sizes == json.loads(TOKENS_JSON.read_text())["type_scale_px"] == [
        11, 12, 13, 14, 16, 20, 24, 32,
    ]  # fmt: skip
    spaces = sorted(int(v[:-2]) for k, v in light.items() if k.startswith("--sp-"))
    assert spaces == [4, 8, 12, 16, 20, 24, 32, 40, 48]
    assert [light[f"--r-{i}"] for i in (1, 2, 3)] == ["3px", "5px", "8px"]
    assert (light["--t-fast"], light["--t-base"]) == ("120ms", "180ms")
    rows = (light["--h-row-comfy"], light["--h-row"], light["--h-row-dense"])
    assert rows == ("44px", "36px", "28px")
    assert light["--h-top"] == "44px"


def test_every_text_pair_is_at_least_4_5_to_1_and_controls_3_to_1_in_both_themes():
    for name, t in zip(("light", "dark"), themes(), strict=True):
        for ink in ("ink", "ink-2", "ink-3", "accent", "ok", "warn", "err", "info", "mute"):
            for ground in ("surface", "bg"):
                ratio = contrast(t["--" + ink], t["--" + ground])
                assert ratio >= 4.5, f"{name}: {ink} on {ground} is {ratio:.2f}"
        for tone in ("ok", "warn", "err", "info", "mute", "accent"):
            ratio = contrast(t["--" + tone], t["--" + tone + "-tint"])
            assert ratio >= 4.5, f"{name}: {tone} on its tint is {ratio:.2f}"
        assert contrast(t["--accent-ink"], t["--accent"]) >= 4.5, name
        assert contrast(t["--line-3"], t["--surface"]) >= 3, f"{name}: line-3"


def test_the_contract_cites_every_rule_the_system_readme_summarises():
    text = (DESIGN / "system/VISUAL_CONTRACT.md").read_text()
    ids = set(re.findall(r"V-[A-Z]+-\d+", text))
    assert {f"V-SLOP-{i}" for i in range(1, 16)} <= ids
    for area in ("TYPE", "SPACE", "DENS", "COLOR", "THEME", "LINE", "ELEV", "RAD", "ICON"):
        assert any(i.startswith(f"V-{area}-") for i in ids), area
    for area in ("MOTION", "FOCUS", "HERO", "RESP"):
        assert any(i.startswith(f"V-{area}-") for i in ids), area


def test_a_failing_pair_is_named_with_its_ratio():
    assert contrast("#777777", "#ffffff") < 4.5
    assert round(contrast("#000000", "#ffffff")) == 21


def board(ref, name):
    return (DESIGN / "references" / ref / "html" / f"{name}.html").read_text()


def test_data_surface_board_keeps_its_must_preserve_contract():
    page = board("organizer-data-surface", "Data-Surface")
    for marker in (
        'role="grid"',
        "aria-rowcount",
        "Select all 243",
        "Frozen snapshot",
        "plan first",
        "virtualized",
        "Reset",
        "Save view",
        "Copy link",
        "registration:confirmed AND waiver:!signed",
        "Restricted",
        "Esc closes",
    ):
        assert marker in page, marker
    assert "ANY OF" in page and "Add group" in page


def test_shell_boards_keep_the_navigation_contract():
    organizer = board("app-shell", "Shell-Organizer")
    for label in ("Manage event", "Advanced", "Operations &amp; audit", "Needs attention"):
        assert label in organizer, label
    assert 'aria-current="page"' in organizer
    assert "Preview as" in organizer
    assert "dialog" in board("app-shell", "Shell-Overlays")
    assert "More" in board("app-shell", "Shell-Mobile")


def test_decision_eleven_is_indexed_and_the_ledger_cites_it():
    assert "011" in (DESIGN / "decisions/README.md").read_text()
    ledger = (DESIGN / "reviews/B00_APPROVAL.md").read_text()
    assert "D-011" in ledger and "approved for implementation" in ledger
