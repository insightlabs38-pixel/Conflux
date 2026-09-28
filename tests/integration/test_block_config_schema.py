import pytest
from django.core.exceptions import ValidationError
from presentation.block_types import BLOCK_TYPES, normalize_config
from presentation.blocks import clean_config
from presentation.models import PageBlockKind


def test_schema_catalog_covers_the_persisted_block_types():
    assert set(BLOCK_TYPES) == set(PageBlockKind.values)


def test_existing_defaults_and_ignored_top_level_keys_remain_compatible():
    assert clean_config("hero", {"title": "Welcome", "legacy": "ignored"}) == {
        "title": "Welcome",
        "subtitle": "",
        "cta_label": "",
        "cta_href": "",
    }
    assert clean_config("gallery", {}) == {"limit": 6}
    assert clean_config("faq", {}) == {"items": []}
    assert clean_config("faq", {"items": [{"question": "Q"}]}) == {
        "items": [{"question": "Q", "answer": ""}],
    }


@pytest.mark.parametrize(
    "kind,config",
    [
        ("hero", {"title": "  "}),
        ("hero", {"title": "x" * 201}),
        ("hero", {"title": 1}),
        ("cta", {"label": "Learn", "href": ""}),
        ("gallery", {"limit": True}),
        ("gallery", {"limit": 1.5}),
        ("gallery", {"limit": 25}),
        ("gallery", {"limit": 0}),
        ("faq", {"items": [{}] * 21}),
        ("faq", {"items": "bad"}),
        ("faq", {"items": [{"answer": "x" * 501}]}),
        ("faq", {"items": [{"script": "bad"}]}),
        ("faq", {"items": ["bad"]}),
        ("tracks", {"limit": 1}),
        ("hero", None),
        ("unknown", {}),
    ],
)
def test_schema_validation_rejects_invalid_persisted_configuration(kind, config):
    with pytest.raises(ValidationError):
        clean_config(kind, config)


def test_rich_text_sanitization_remains_a_server_boundary():
    assert clean_config(
        "rich_text", {"html": '<p onclick="evil()">Hi<script>evil()</script></p>'}
    ) == {"html": "<p>Hi</p>"}


def test_explicit_null_is_not_reinterpreted_as_an_omitted_optional_field():
    with pytest.raises(ValidationError):
        clean_config("hero", {"title": "Hello", "subtitle": None})


def test_code_level_declarations_drive_validation_without_kind_dispatch(monkeypatch):
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "capacity": {"type": "integer", "minimum": 1, "maximum": 4, "default": 2},
        },
    }
    monkeypatch.setitem(BLOCK_TYPES, "example", {"title": "Example", "schema": schema})
    assert clean_config("example", {}) == {"capacity": 2}
    with pytest.raises(ValidationError):
        clean_config("example", {"capacity": 5})
    with pytest.raises(ValidationError):
        normalize_config({"type": "unknown"}, "unsafe")
