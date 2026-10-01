"""PD-F002-B02-T01: the platform schema subset, its conformance and its first adopters."""

import json
import pathlib
from copy import deepcopy

import pytest
from core import schema_subset as subset
from django.core.exceptions import ValidationError
from presentation.block_types import BLOCK_TYPES, normalize_config

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/fixtures/schema_cases.json").read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_the_shared_fixtures_hold(case):
    """The same file is run by vitest against the browser implementation."""
    problems = subset.validate(case["schema"], case["value"])
    expected = case.get("problems", [])
    assert [{"path": p.path, "code": p.code} for p in problems] == expected
    if not expected:
        assert subset.normalize(case["schema"], case["value"]) == case["normalized"]


def legacy_normalize_config(schema, value, path="config"):
    """A frozen copy of `presentation.block_types.normalize_config` as it was before it adopted
    the shared validator; the oracle the adoption is held to."""
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict):
            raise ValidationError({path: "Must be an object."})
        properties = schema["properties"]
        if not schema["additionalProperties"] and value.keys() - properties.keys():
            raise ValidationError({path: "Unknown fields."})
        return {
            key: legacy_normalize_config(field, value.get(key, deepcopy(field["default"])), key)
            for key, field in properties.items()
        }
    if kind == "string":
        if not isinstance(value, str):
            raise ValidationError({path: "Must be text."})
        if schema.get("x-nonblank") and not value.strip():
            raise ValidationError({path: "This field is required."})
        if len(value) > schema["maxLength"]:
            raise ValidationError({path: f"Must be at most {schema['maxLength']} characters."})
        return value
    if kind == "integer":
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not schema["minimum"] <= value <= schema["maximum"]
        ):
            raise ValidationError(
                {path: f"Must be an integer from {schema['minimum']} to {schema['maximum']}."}
            )
        return value
    if kind == "array":
        if not isinstance(value, list) or len(value) > schema["maxItems"]:
            raise ValidationError({path: f"Must be a list of at most {schema['maxItems']} items."})
        return [legacy_normalize_config(schema["items"], item, path) for item in value]
    raise ValidationError({path: "Unsupported configuration type."})


def outcome(function, schema, value):
    try:
        return ("ok", function(schema, deepcopy(value)))
    except ValidationError as exc:
        return ("error", exc.message_dict)


def candidate_values(schema):
    """Deterministic values around every property of a block: starting points, the boundaries and
    the wrong types, nested the way the schema nests."""
    base = subset.defaults(schema)
    yield {}
    yield base
    yield subset.defaults(schema, creating=True)
    yield None
    yield []
    yield "text"
    yield {**base, "unknown_key": "x"}
    for name, field in schema["properties"].items():
        kind = field["type"]
        wrong = {"string": 5, "integer": "1", "array": "x"}[kind]
        yield {**base, name: wrong}
        yield {**base, name: None}
        if kind == "string":
            yield {**base, name: "x" * field["maxLength"]}
            yield {**base, name: "x" * (field["maxLength"] + 1)}
            yield {**base, name: "   "}
            yield {**base, name: "ok"}
        if kind == "integer":
            for edge in (
                field["minimum"],
                field["maximum"],
                field["minimum"] - 1,
                field["maximum"] + 1,
                True,
                1.5,
            ):
                yield {**base, name: edge}
        if kind == "array":
            row = {k: "v" for k in field["items"]["properties"]}
            yield {**base, name: [row] * field["maxItems"]}
            yield {**base, name: [row] * (field["maxItems"] + 1)}
            yield {**base, name: [{**row, "extra": "no"}]}
            yield {**base, name: ["not a row"]}
            yield {**base, name: [{"label": 5}]}


@pytest.mark.parametrize("kind", sorted(BLOCK_TYPES))
def test_every_block_schema_validates_exactly_as_before(kind):
    schema = BLOCK_TYPES[kind]["schema"]
    count = 0
    for value in candidate_values(schema):
        assert outcome(normalize_config, schema, value) == outcome(
            legacy_normalize_config, schema, value
        ), (kind, value)
        count += 1
    assert count >= 7  # blocks with no properties have only the structural cases


def test_every_block_schema_is_inside_the_subset_and_its_defaults_hold():
    for kind, block in BLOCK_TYPES.items():
        assert subset.check(block["schema"]) == [], kind
        assert subset.defaults(block["schema"]) is not None


def test_every_setting_schema_of_the_registry_is_inside_the_subset():
    from eventconfig.registry import SPECS

    for spec in SPECS:
        assert subset.check(spec.schema) == [], spec.key


@pytest.mark.parametrize(
    "schema,fragment",
    [
        ({"type": "string", "pattern": "x"}, "unsupported keywords pattern"),
        ({"type": "string", "$ref": "#/x"}, "unsupported keywords $ref"),
        ({"type": "uuid"}, "type must be one of"),
        ({"type": ["string", "integer"]}, "type must be one of"),
        ({"type": ["string", "null"], "enum": []}, "enum must be a non-empty list"),
        ({"type": "object"}, "needs properties"),
        ({"type": "array"}, "needs items"),
        ({"type": "string", "x-widget": "carousel"}, "x-widget"),
        ({"type": "string", "format": "email"}, "format must be date-time"),
        (
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["b"]},
            "required",
        ),
        ({"type": "string", "maxLength": 2, "default": "toolong"}, "default does not satisfy"),
        ("string", "must be an object"),
    ],
)
def test_a_schema_outside_the_subset_is_named(schema, fragment):
    problems = subset.check(schema)
    assert problems and any(fragment in p for p in problems), problems


def test_platform_caps_apply_when_a_schema_gives_no_bound():
    assert subset.validate({"type": "string"}, "x" * subset.MAX_STRING) == []
    assert (
        subset.validate({"type": "string"}, "x" * (subset.MAX_STRING + 1))[0].code == "max_length"
    )
    items = {"type": "array", "items": {"type": "integer"}}
    assert subset.validate(items, list(range(subset.MAX_ARRAY + 1)))[0].code == "max_items"
    deep = {"type": "string"}
    for _ in range(subset.MAX_DEPTH + 2):
        deep = {"type": "object", "properties": {"a": deep}}
    value = current = {}
    for _ in range(subset.MAX_DEPTH + 2):
        current["a"] = {}
        current = current["a"]
    assert any(p.code == "depth" for p in subset.validate(deep, value))


def test_normalising_is_pure_and_the_api_error_shape_is_keyed_by_path():
    schema = {
        "type": "object",
        "properties": {"rows": {"type": "array", "items": {"type": "string", "maxLength": 1}}},
    }
    value = {"rows": ["a", "bb"]}
    before = deepcopy(value)
    with pytest.raises(subset.SchemaError) as caught:
        subset.normalize(schema, value)
    assert value == before
    assert subset.api_errors(caught.value.problems) == {
        "rows[1]": ["Must be at most 1 characters."]
    }
    assert subset.api_errors(subset.validate({"type": "boolean"}, 1)) == {
        "value": ["Must be true or false."]
    }
    defaults_before = deepcopy(BLOCK_TYPES["hero"]["schema"])
    subset.defaults(BLOCK_TYPES["hero"]["schema"]).update({"title": "mutated"})
    assert BLOCK_TYPES["hero"]["schema"] == defaults_before


def test_a_validation_never_raises_on_hostile_input():
    schema = (
        BLOCK_TYPES["gallery_strip"]["schema"]
        if "gallery_strip" in BLOCK_TYPES
        else next(iter(BLOCK_TYPES.values()))["schema"]
    )
    hostile = [
        None,
        True,
        1e308,
        float("inf"),
        "\x00" * 10,
        {"a": {"b": {"c": []}}},
        [[[]]],
        {"__proto__": 1},
    ]
    for value in hostile:
        subset.validate(schema, value)
        subset.validate({"type": "number"}, value)
        subset.validate({"type": ["string", "null"], "maxLength": 3}, value)
