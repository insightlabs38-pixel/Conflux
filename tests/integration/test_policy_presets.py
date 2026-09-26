import pytest
from policies.evaluator import PolicyError, evaluate
from policies.presets import PRESETS, build_preset_ast


def test_every_preset_produces_a_structurally_valid_ast():
    from policies.evaluator import validate_structure

    for slug, preset in PRESETS.items():
        params = {p: "x" for p in preset["params"]}
        ast = build_preset_ast(slug, params)
        validate_structure(ast)  # must not raise


def test_everyone_preset_always_allows():
    ast = build_preset_ast("everyone")
    assert evaluate(ast, {}) is True


def test_no_one_preset_always_denies():
    ast = build_preset_ast("no_one")
    assert evaluate(ast, {}) is False


def test_organizers_only_preset_checks_the_role_fact():
    ast = build_preset_ast("organizers_only")
    assert evaluate(ast, {"role": "organizer"}) is True
    assert evaluate(ast, {"role": "participant"}) is False


def test_window_open_preset_references_the_named_gate():
    ast = build_preset_ast("window_open", {"gate_name": "submissions"})
    assert evaluate(ast, {"gate_open:submissions": True}) is True
    assert evaluate(ast, {"gate_open:submissions": False}) is False


def test_window_open_preset_requires_gate_name():
    with pytest.raises(PolicyError, match="needs: gate_name"):
        build_preset_ast("window_open", {})


def test_unknown_preset_raises():
    with pytest.raises(PolicyError, match="Unknown preset"):
        build_preset_ast("does_not_exist")
