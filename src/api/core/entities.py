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
LIST, BOARD, MATRIX, CALENDAR = "list", "board", "matrix", "calendar"
LAYOUTS = (LIST, BOARD, MATRIX, CALENDAR)
SUM, AVG, MIN, MAX = "sum", "avg", "min", "max"
# What may be summarised, by field type: a number any of them, a date only its range.
AGGREGATES = {NUMBER: (SUM, AVG, MIN, MAX), DATE: (MIN, MAX)}

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
    # May rows be grouped by it (PD-F006-B02-T08): a field with a modest number of distinct values.
    groupable: bool = False
    # How to read the value off a row when the column path is not enough.
    read: Callable[[Any], Any] | None = None
    # The footer values that mean something for this field (PD-F006-B03-T02); None takes what its
    # type allows (a sum of waitlist positions would not, so such a field narrows it).
    aggregates: tuple | None = None

    def summaries(self):
        """The aggregate functions this field offers, from its type and any narrowing."""
        allowed = AGGREGATES.get(self.type, ())
        return allowed if self.aggregates is None else self.aggregates


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
    # Keys of the TEXT fields a free-text search looks in; empty means the list has no search box.
    search_fields: tuple = ()
    # The groupable field whose values are the columns of a board (a workflow-like field), and the
    # DATE fields a calendar may place rows on (PD-F006-B03-T01). Empty means that layout is not
    # meaningful for the list and is not offered.
    board_field: str = ""
    calendar_fields: tuple = ()

    def field(self, key):
        return next((f for f in self.fields if f.key == key), None)

    def layouts(self):
        """The ways this list may be laid out, from what is registered: a list always; a board
        when a board field is named; a matrix when two fields can be grouped; a calendar when a
        date field may place rows."""
        found = [LIST]
        if self.board_field:
            found.append(BOARD)
        if sum(1 for f in self.fields if f.groupable) >= 2:
            found.append(MATRIX)
        if self.calendar_fields:
            found.append(CALENDAR)
        return found


_ENTITIES: dict[str, Entity] = {}
_discovered = False


def register(entity: Entity):
    """Register an entity once: a second, different registration under a key is a bug."""
    for f in entity.fields:
        if f.type not in TYPES:
            raise ValueError(f"{entity.key}.{f.key}: unknown field type {f.type!r}")
        if f.type == ENUM and not f.choices:
            raise ValueError(f"{entity.key}.{f.key}: an enum field needs choices")
        for fn in f.aggregates or ():
            if fn not in AGGREGATES.get(f.type, ()):
                raise ValueError(
                    f"{entity.key}.{f.key}: a {f.type} field cannot be summed as {fn!r}"
                )
    for key in entity.search_fields:
        found = entity.field(key)
        if found is None or found.type != TEXT:
            raise ValueError(f"{entity.key}: search field {key!r} must be a registered text field")
    if entity.board_field:
        found = entity.field(entity.board_field)
        if found is None or not found.groupable:
            raise ValueError(f"{entity.key}: board field {entity.board_field!r} must be groupable")
    for key in entity.calendar_fields:
        found = entity.field(key)
        if found is None or found.type != DATE or not found.filterable:
            raise ValueError(f"{entity.key}: calendar field {key!r} must be a filterable date")
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
