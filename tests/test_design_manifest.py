"""The committed Claude Design handoff is the design authority; its manifest must resolve."""

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
