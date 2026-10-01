"""The platform schema subset: one validator for every code-owned configuration shape
(PD-F002-B02-T01).

A schema is plain JSON, owned by code (a page block, a setting, a form of an extension): a client
never supplies one, and the endpoint that owns a value still validates it itself. The subset is a
documented slice of JSON Schema, small enough that the server (this module) and the browser
(`src/web/lib/schema.ts`) implement it identically; `tests/fixtures/schema_cases.json` is run by
both so they cannot drift.

Keywords
- `type`: `object`, `string`, `integer`, `number`, `boolean`, `array`; a list adds `"null"`
  (`["integer", "null"]`). Booleans are never numbers.
- `enum` (any scalar type), `default`, `title`, `description`.
- string: `minLength`, `maxLength`, `format: "date-time"` (explicit offset required);
  number and integer: `minimum`, `maximum`; array: `items`, `minItems`, `maxItems`, `uniqueItems`;
  object: `properties`, `required`, `additionalProperties` (true drops unknown keys when
  normalising, false rejects them).
- UI hints that never affect validation: `x-widget` (`input`, `textarea`, `select`, `switch`,
  `datetime`), `x-help`, `x-create-default`; and `x-nonblank` (a string needs non-whitespace text).

No `$ref`, composition (`oneOf`, `allOf`), conditionals or patterns: nothing a client can send
makes validation expensive. Strings and arrays without a bound get a platform cap.

Normalising an object keeps only the declared properties, in declaration order, filling omitted
ones from their `default`; a property without a default that is not `required` stays absent.
"""

import math
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime

MAX_STRING = 100_000
MAX_ARRAY = 1_000
MAX_DEPTH = 8
TYPES = {"object", "string", "integer", "number", "boolean", "array", "null"}
WIDGETS = {"input", "textarea", "select", "switch", "datetime"}
KEYWORDS = {
    "type", "enum", "default", "title", "description", "minLength", "maxLength", "format",
    "minimum", "maximum", "items", "minItems", "maxItems", "uniqueItems", "properties",
    "required", "additionalProperties", "x-widget", "x-help", "x-create-default", "x-nonblank",
}  # fmt: skip


@dataclass(frozen=True)
class Problem:
    """One thing wrong with a value: where (`items[2].name`, "" for the root), a stable `code`
    and a sentence."""

    path: str
    code: str
    message: str


class SchemaError(Exception):
    def __init__(self, problems):
        super().__init__("; ".join(f"{p.path or 'value'}: {p.message}" for p in problems))
        self.problems = problems


def _types(schema):
    kind = schema.get("type")
    return list(kind) if isinstance(kind, list) else [kind]


def check(schema, path="") -> list[str]:
    """What is wrong with the *schema itself* (empty when it is inside the subset)."""
    if not isinstance(schema, dict):
        return [f"{path or 'schema'}: must be an object"]
    problems = []
    where = path or "schema"
    unknown = set(schema) - KEYWORDS
    if unknown:
        problems.append(f"{where}: unsupported keywords {', '.join(sorted(unknown))}")
    kinds = _types(schema)
    if not kinds or any(k not in TYPES for k in kinds) or (len(kinds) > 1 and "null" not in kinds):
        problems.append(f"{where}: type must be one of {sorted(TYPES)} (a list only adds null)")
        return problems
    if len([k for k in kinds if k != "null"]) != 1:
        problems.append(f"{where}: needs exactly one non-null type")
        return problems
    kind = [k for k in kinds if k != "null"][0]
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        problems.append(f"{where}: enum must be a non-empty list")
    if schema.get("x-widget") is not None and schema["x-widget"] not in WIDGETS:
        problems.append(f"{where}: x-widget must be one of {sorted(WIDGETS)}")
    if schema.get("format") not in (None, "date-time"):
        problems.append(f"{where}: format must be date-time")
    if kind == "object":
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            problems.append(f"{where}: an object needs properties")
        else:
            for name, field in properties.items():
                problems += check(field, f"{path}.{name}" if path else name)
        extra = schema.get("required", [])
        if not isinstance(extra, list) or any(r not in (properties or {}) for r in extra):
            problems.append(f"{where}: required must name declared properties")
    if kind == "array":
        if not isinstance(schema.get("items"), dict):
            problems.append(f"{where}: an array needs items")
        else:
            problems += check(schema["items"], f"{path}[]")
    # A required text field's default is empty on purpose: `x-create-default` supplies the start.
    if "default" in schema and not schema.get("x-nonblank") and validate(schema, schema["default"]):
        problems.append(f"{where}: the default does not satisfy the schema")
    return problems


def defaults(schema, creating=False):
    """The starting value of an object schema: each property's default (`x-create-default` first
    when creating something new)."""
    out = {}
    for name, field in (schema.get("properties") or {}).items():
        chosen = field.get("x-create-default") if creating else None
        if chosen is None:
            chosen = field.get("default")
        if chosen is not None or "default" in field:
            out[name] = deepcopy(chosen)
    return out


def _join(path, key):
    return f"{path}.{key}" if path else key


def _walk(schema, value, path, depth, problems, out_holder):
    """Validate `value` and build its normalised form into `out_holder[0]`."""
    if depth > MAX_DEPTH:
        problems.append(Problem(path, "depth", "Nested too deeply."))
        return
    kinds = _types(schema)
    nullable = "null" in kinds
    kind = [k for k in kinds if k != "null"][0]
    if value is None and nullable:
        out_holder[0] = None
        return
    if "enum" in schema and value not in schema["enum"]:
        listed = ", ".join(str(v) for v in schema["enum"])
        problems.append(Problem(path, "enum", f"Must be one of: {listed}."))
        return
    if kind == "object":
        if not isinstance(value, dict):
            problems.append(Problem(path, "type", "Must be an object."))
            return
        properties = schema["properties"]
        if schema.get("additionalProperties", True) is False and value.keys() - properties.keys():
            problems.append(Problem(path, "unknown_fields", "Unknown fields."))
        required = set(schema.get("required", []))
        result = {}
        for name, field in properties.items():
            child = _join(path, name)
            if name in value:
                holder = [None]
                _walk(field, value[name], child, depth + 1, problems, holder)
                result[name] = holder[0]
            elif "default" in field:
                holder = [None]
                _walk(field, deepcopy(field["default"]), child, depth + 1, problems, holder)
                result[name] = holder[0]
            elif name in required:
                problems.append(Problem(child, "required", "This field is required."))
        out_holder[0] = result
        return
    if kind == "string":
        if not isinstance(value, str):
            problems.append(Problem(path, "type", "Must be text."))
            return
        if schema.get("x-nonblank") and not value.strip():
            problems.append(Problem(path, "required", "This field is required."))
            return
        longest = schema.get("maxLength", MAX_STRING)
        if len(value) > longest:
            problems.append(Problem(path, "max_length", f"Must be at most {longest} characters."))
            return
        shortest = schema.get("minLength", 0)
        if len(value) < shortest:
            problems.append(Problem(path, "min_length", f"Must be at least {shortest} characters."))
            return
        if schema.get("format") == "date-time" and not _aware_instant(value):
            problems.append(Problem(path, "format", "Must be a date and time with a UTC offset."))
            return
        out_holder[0] = value
        return
    if kind in ("integer", "number"):
        noun = "an integer" if kind == "integer" else "a number"
        low, high = schema.get("minimum"), schema.get("maximum")
        if low is not None and high is not None:
            wording = f"Must be {noun} from {low} to {high}."
        elif low is not None:
            wording = f"Must be {noun} of at least {low}."
        elif high is not None:
            wording = f"Must be {noun} of at most {high}."
        else:
            wording = f"Must be {noun}."
        whole = isinstance(value, int) and not isinstance(value, bool)
        real = isinstance(value, float) and math.isfinite(value)
        if not (whole or (kind == "number" and real)):
            problems.append(Problem(path, "type", wording))  # one sentence for type and range
            return
        if (low is not None and value < low) or (high is not None and value > high):
            problems.append(Problem(path, "range", wording))
            return
        out_holder[0] = value
        return
    if kind == "boolean":
        if not isinstance(value, bool):
            problems.append(Problem(path, "type", "Must be true or false."))
            return
        out_holder[0] = value
        return
    if kind == "array":
        most = schema.get("maxItems", MAX_ARRAY)
        if not isinstance(value, list) or len(value) > most:
            problems.append(Problem(path, "max_items", f"Must be a list of at most {most} items."))
            return
        fewest = schema.get("minItems", 0)
        if len(value) < fewest:
            problems.append(
                Problem(path, "min_items", f"Must be a list of at least {fewest} items.")
            )
            return
        items = []
        for index, item in enumerate(value):
            holder = [None]
            _walk(schema["items"], item, f"{path}[{index}]", depth + 1, problems, holder)
            items.append(holder[0])
        if schema.get("uniqueItems") and len({repr(i) for i in items}) != len(items):
            problems.append(Problem(path, "unique", "Must not repeat an item."))
            return
        out_holder[0] = items
        return
    problems.append(Problem(path, "unsupported", "Unsupported configuration type."))


_INSTANT = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:\d\d)$")


def _aware_instant(text):
    """An ISO 8601 date and time with an explicit offset (the browser applies the same test)."""
    if not _INSTANT.match(text):
        return False
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate(schema, value) -> list[Problem]:
    """Every problem with `value`, in traversal order (properties in declaration order)."""
    problems = []
    _walk(schema, value, "", 0, problems, [None])
    return problems


def normalize(schema, value):
    """The normalised value, or `SchemaError` listing every problem."""
    problems = []
    holder = [None]
    _walk(schema, value, "", 0, problems, holder)
    if problems:
        raise SchemaError(problems)
    return holder[0]


def api_errors(problems) -> dict:
    """The 400 body shape: `{path: [messages]}`, the root as `value`."""
    out = {}
    for problem in problems:
        out.setdefault(problem.path or "value", []).append(problem.message)
    return out
