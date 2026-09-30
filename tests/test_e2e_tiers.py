"""Selection logic of scripts/e2e-tiers (PD-B03-T06): pure functions, no browser or stack needed."""

import json
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_loader = SourceFileLoader("e2e_tiers", str(ROOT / "scripts/e2e-tiers"))
tiers = module_from_spec(spec_from_loader("e2e_tiers", _loader))
_loader.exec_module(tiers)


def test_every_spec_is_classified_exactly_once_and_mappings_name_real_specs():
    assert tiers.check() == []


def test_smoke_is_cheap_read_only_reference_coverage():
    cfg = json.loads((ROOT / "tests/e2e/affected.json").read_text())
    assert {tiers.tier_of(s) for s in cfg["smoke"]} == {"read-only"}
    assert len(cfg["smoke"]) <= 4


@pytest.mark.parametrize(
    ("paths", "specs"),
    [
        (["src/web/features/pvs/PvsPanel.tsx"], ["pvs"]),
        (
            ["src/web/features/judging/JudgeDesk.tsx"],
            ["lifecycle", "uiv2-final-states", "uiv2-gate", "uiv2-judge", "uiv2-organizer"],
        ),
        (["src/api/mentorship/services.py"], ["pvs"]),
        (["src/embed/src/gallery.ts"], ["extended-embed", "public"]),
        (["tests/e2e/profiles.spec.ts"], ["profiles"]),
        (
            ["src/api/accounts/views.py", "src/web/features/profile/Profile.tsx"],
            ["auth-states", "profiles", "roles", "signin", "workspace-shell"],
        ),
    ],
)
def test_changed_paths_select_the_mapped_specs(paths, specs):
    selected, reasons = tiers.select_affected(paths)
    assert selected == specs and len(reasons) == len(paths)


@pytest.mark.parametrize(
    "path",
    [
        "src/web/components/Button.tsx",
        "src/web/styles/tokens.css",
        "tests/e2e/support.ts",
        "scripts/e2e-stack",
        "Makefile",
    ],
)
def test_shared_infrastructure_selects_everything(path):
    assert tiers.select_affected([path, "docs/operations/E2E.md"])[0] is None


def test_docs_tests_and_non_source_paths_select_nothing():
    selected, _ = tiers.select_affected(
        ["docs/operations/E2E.md", "README.md", "src/web/features/pvs/Pvs.test.tsx", "uv.lock"]
    )
    assert selected == []


def test_unmapped_source_falls_back_to_smoke_with_a_visible_reason():
    selected, reasons = tiers.select_affected(["src/api/taxonomy/models.py"])
    assert selected == ["public", "roles", "signin"]
    assert "unmapped" in reasons[0]


def test_canary_selection_runs_the_chain_prefix_the_selected_spec_depends_on():
    assert tiers.canary_chain(["uiv2-organizer"]) == ["lifecycle", "scenes", "uiv2-organizer"]
    assert tiers.canary_chain(["lifecycle"]) == ["lifecycle"]
    assert tiers.canary_chain() == tiers.tiers()["canary"]


@pytest.mark.parametrize("count", range(1, 9))
def test_shards_partition_every_work_unit_exactly_once(count):
    everything = sorted(u[0] for u in tiers.units())
    assigned = sorted(u[0] for _, members in tiers.split(count) for u in members)
    assert assigned == everything


def test_sharding_is_deterministic_and_keeps_the_canary_chain_whole():
    assert tiers.split(4) == tiers.split(4)
    holders = [i for i in range(1, 5) if "canary" in tiers.shard_selection(i, 4)]
    assert len(holders) == 1
    assert (
        tiers.canary_chain(tiers.shard_selection(holders[0], 4)["canary"])
        == tiers.tiers()["canary"]
    )


@pytest.mark.parametrize("count", [2, 3, 4, 6])
def test_shards_are_balanced_within_the_greedy_bound(count):
    shards = tiers.split(count)
    total = sum(seconds for seconds, _ in shards)
    largest = max(tiers.weights().values())
    assert max(seconds for seconds, _ in shards) <= total / count + largest


def test_every_unit_has_a_measured_weight():
    # A new spec needs `scripts/e2e-tiers weights`; otherwise sharding guesses the median weight.
    assert {u[0] for u in tiers.units()} <= set(tiers.weights())


@pytest.mark.parametrize("bad", ["0/4", "5/4", "x", "2/0", "1-4"])
def test_shard_argument_is_validated(bad):
    with pytest.raises(SystemExit):
        tiers.parse_shard(bad)
