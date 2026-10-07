"""PD-F005-B01-T06: global search finds records through the universal query engine, so every
registered query entity must say how it is found and where a hit opens. The entries live in
src/web/lib/searchTargets.json, which the app reads too; a new entity fails here until it has
one."""

import json
import pathlib

from core import entities

ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGETS = json.loads((ROOT / "src/web/lib/searchTargets.json").read_text(encoding="utf-8"))


def test_every_registered_entity_has_a_search_target_and_nothing_else_does():
    assert set(entities.entities()) == set(TARGETS)


def test_the_label_and_detail_fields_exist_and_the_label_can_be_searched_by_contains():
    for key, target in TARGETS.items():
        entity = entities.entities()[key]
        label = entity.field(target["labelField"])
        assert label is not None, f"{key}: no field {target['labelField']}"
        assert label.type == entities.TEXT and label.filterable, key
        assert "contains" in entities.OPERATORS[label.type]
        if target.get("detailField"):
            assert entity.field(target["detailField"]) is not None, key
        assert target["view"] and target["noun"] and target["nouns"], key


def test_a_hit_opens_a_view_the_organizer_has():
    # the destinations of the organizer shell (src/web/components/WorkspaceNavigation.tsx)
    source = (ROOT / "src/web/components/WorkspaceNavigation.tsx").read_text(encoding="utf-8")
    organizer = source[source.index("  organizer: [") : source.index("  mentor: [")]
    for key, target in TARGETS.items():
        assert f'id: "{target["view"]}"' in organizer, f"{key}: unknown view {target['view']}"
