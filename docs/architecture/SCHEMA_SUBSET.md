# Schema subset (SCHEMA_EDITOR)

One validator and one editor for every code-owned configuration shape: page blocks, event settings and whatever a feature declares next. Server `core/schema_subset.py`, browser `src/web/lib/schema.ts` and the form `src/web/components/SchemaForm.tsx`.

## What a schema is

A documented slice of JSON Schema, small enough that two implementations agree exactly.

| Keyword                                   | Meaning                                                                                                                                 |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `type`                                    | `object`, `string`, `integer`, `number`, `boolean`, `array`; a list adds `"null"` (`["integer", "null"]`). A boolean is never a number. |
| `enum`, `default`, `title`, `description` | allowed values, the value used when a property is omitted, the label, a hint                                                            |
| string                                    | `minLength`, `maxLength` (counted in characters), `format: "date-time"` (explicit offset required)                                      |
| `integer`, `number`                       | `minimum`, `maximum`                                                                                                                    |
| `array`                                   | `items`, `minItems`, `maxItems`, `uniqueItems`                                                                                          |
| `object`                                  | `properties`, `required`, `additionalProperties` (false rejects unknown keys; true drops them when normalising)                         |
| UI hints                                  | `x-widget` (`input`, `textarea`, `select`, `switch`, `datetime`), `x-help`, `x-create-default` (the starting text when creating)        |
| rule                                      | `x-nonblank`: a string needs non-whitespace text                                                                                        |

Not supported on purpose: `$ref`, `oneOf`/`allOf`, conditionals, patterns. Strings and arrays without a bound get a platform cap (100,000 characters, 1,000 items) and nesting stops at depth 8, so nothing a client sends makes validation expensive. `check(schema)` names anything outside the subset.

## Using it

Server: `validate(schema, value)` returns every problem as `Problem(path, code, message)` in traversal order (`rows[2].name`, "" for the value itself); `normalize` returns the value with defaults filled and unknown keys dropped or `SchemaError`; `defaults(schema, creating)`; `api_errors(problems)` gives the 400 body keyed by path. Browser: the same functions plus `sentence(problem)` ("Title is required."). `SchemaForm` takes the schema, the value, `onChange`, the problems and an optional `timeZone` for date-times, and renders one control per property: text or textarea, select for an enum, checkbox for a boolean, number with min and max, date-time on the event's clock stored as a UTC instant, a checkbox group for an array of enum values, rows (with the declared cap) for arrays of objects or scalars.

## Rules

- **Schemas are code-owned.** A client never supplies one, and the endpoint that owns a value validates it again; the browser check only saves a round trip and points at the field.
- **The two implementations cannot drift.** `tests/fixtures/schema_cases.json` (42 cases: paths and codes, in order) is run by pytest (`tests/integration/test_schema_subset.py`) and vitest (`src/web/lib/schema.test.ts`).
- **Adoption is byte-compatible.** `presentation.block_types.normalize_config` now delegates to the subset; a frozen copy of the previous function is the oracle in the test, and hundreds of generated values on all 12 block schemas must give the same verdict, value and message. The page builder's `ConfigFields` renders through `SchemaForm`; its generated catalogue and public rendering are unchanged.
- **Settings are editable in place.** Setup > Defaults & overrides shows a Change control for every setting the configuration answer marks editable (and whose module is on): the form is the setting's own schema, the save goes to the `write` endpoint the answer names (an endpoint that replaces everything is read first), so the domain's validation, locks, audit and versioning decide. A value the schema refuses is never sent; the domain's refusal is shown with the form left open.

## Compatibility

Stateless and additive: no table, no migration, no API change. Existing block configuration, public pages and the generated block schema catalogue (`make block-schema-check`) are untouched.
