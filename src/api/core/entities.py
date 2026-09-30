"""The entity catalogue behind the universal query engine (PD-F002-B01-T01).

A domain registers what may be listed, filtered and sorted about its rows; `core.query` compiles a
client's query against that registration and nothing else. Authorization is decided here, once:
`roles` says who may query the entity and `base` returns the rows that person may see for the
event, so the generic code can neither widen a result nor reach a column nobody registered.
Domains register from an `entities` module in their own app; `core` never imports them.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from django.utils.module_loading import autodiscover_modules

TEXT, NUMBER, DATE, BOOL, ENUM, UUID = "text", "number", "date", "bool", "enum", "uuid"
TYPES = (TEXT, NUMBER, DATE, BOOL, ENUM, UUID)

# The operators each field type offers. Anything else is refused with the list of these.
OPERATORS = {
    TEXT: ("eq", "ne", "in", "contains", "startswith", "is_null"),
    NUMBER: ("eq", "ne", "lt", "lte", "gt", "gte", "between", "in", "is_null"),
    DATE: ("lt", "lte", "gt", "gte", "between", "is_null"),
    BOOL: ("eq", "is_null"),
    ENUM: ("eq", "ne", "in", "is_null"),
    UUID: ("eq", "in", "is_null"),
}


@dataclass(frozen=True)
class Field:
    key: str
    type: str
    column: str  # ORM path of the stored value (forward relations only)
    label: str
    sortable: bool = True
    filterable: bool = True
    choices: tuple = ()  # allowed values of an enum field
    default: bool = True  # shown when the client names no columns
    # How to read the value off a row when the column path is not enough.
    read: Callable[[Any], Any] | None = None


@dataclass(frozen=True)
class Entity:
    key: str
    label: str
    roles: tuple  # workspace roles that may query it
    base: Callable[
        [Any, Any], Any
    ]  # (event, user) -> QuerySet already limited to what they may see
    fields: tuple = field(default_factory=tuple)
    default_sort: tuple = ()  # e.g. ("-created_at",)

    def field(self, key):
        return next((f for f in self.fields if f.key == key), None)


_ENTITIES: dict[str, Entity] = {}
_discovered = False


def register(entity: Entity):
    """Register an entity once: a second, different registration under a key is a bug."""
    for f in entity.fields:
        if f.type not in TYPES:
            raise ValueError(f"{entity.key}.{f.key}: unknown field type {f.type!r}")
        if f.type == ENUM and not f.choices:
            raise ValueError(f"{entity.key}.{f.key}: an enum field needs choices")
    if entity.key in _ENTITIES and _ENTITIES[entity.key] != entity:
        raise ValueError(f"Entity {entity.key!r} is already registered")
    _ENTITIES[entity.key] = entity
    return entity


def entities() -> dict[str, Entity]:
    global _discovered
    if not _discovered:
        _discovered = True
        autodiscover_modules("entities")
    return _ENTITIES


def get(key):
    return entities().get(key)
