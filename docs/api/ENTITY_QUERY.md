# Entity query (universal list, filter and sort)

One contract for listing rows of a registered entity in an event. New list features use it instead of parsing their own query parameters. Stateless: nothing is stored (saved views, PD-F002-B01-T02, store a query, never rows).

## Endpoints

Workspace members only; an entity additionally names the roles that may query it (applications and projects: organizer and admin).

- `GET /workspaces/{w}/events/{e}/entities/` lists what the caller may query, with each field's `type`, `operators`, `choices`, `sortable`, `filterable` and whether it is a default column.
- `GET /workspaces/{w}/events/{e}/entities/{entity}/` returns `{entity, total, limit, offset, filter, sort, columns, rows}`. Every row has `id` (the public id) and the requested columns.

| Parameter           | Meaning                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `filter`            | Compact JSON filter tree (below). Empty: no filter.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `sort`              | Comma list of sortable fields, `-` for descending, at most 3. The entity default applies when empty; the primary key always breaks ties.                                                                                                                                                                                                                                                                                                                                                        |
| `columns`           | Comma list of registered fields to return; default: the entity's default columns.                                                                                                                                                                                                                                                                                                                                                                                                               |
| `search`            | Free text (PD-F006-B01): whitespace-separated words, at most 5 of 2 to 200 characters; every word must appear, case-insensitively, in at least one of the entity's `search_fields` (listed in the catalogue; an entity without them cannot be searched and answers 400). Combined with `filter`; a page echoes it as `search`.                                                                                                                                                                  |
| `group`, `subgroup` | A field the catalogue marks `groupable` (and a second, different one inside it). The response then lists `groups` - each with `key`, `label`, `null`, `count` and, with a subgroup, `subgroups` - for the current filter and search, empty values last as `(none)`, at most 200 groups (`truncated` says so), and no rows. Open a bucket with the ordinary query and the bucket's value as one more condition (`eq`, or `is_null` for `(none)`). A saved view may carry `group` and `subgroup`. |
| `limit`, `offset`   | `limit` 1..100 (default 25), `offset` >= 0.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

Empty values sort last in both directions, so the order reads the same on every database, and a counted `total` is returned with every page.

## From the CLI and from an agent

`scripts/conflux-admin entities list EVENT` and `scripts/conflux-admin entities query EVENT projects --search robot --sort=-name --columns name --limit 25` run these same two reads (write `--sort=-name` with an equals sign). The MCP tool `query_entity` takes the entity key and the same `filter`, `sort`, `columns`, `search`, `limit` and `offset`. Both are read-only, run as the credential and are refused exactly as the route refuses them.

## Filter tree

A node is a group, `{"and": [...]}`, `{"or": [...]}` or `{"not": node}`, or a condition `{"field": "status", "op": "eq", "value": "pending"}`. Limits: nesting 4 deep, 20 conditions, 50 values in `in`, 200 characters per text value.

| Field type | Operators                                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------------------------- |
| text       | `eq`, `ne`, `in`, `contains` (case-insensitive), `startswith` (case-insensitive), `is_null`                         |
| number     | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `between`, `in`, `is_null`                                                    |
| date       | `lt`, `lte`, `gt`, `gte`, `between`, `is_null` (ISO 8601; a date without a time means the start of that day in UTC) |
| bool       | `eq`, `is_null`                                                                                                     |
| enum       | `eq`, `ne`, `in`, `is_null` (value must be one of the field's `choices`)                                            |
| uuid       | `eq`, `in`, `is_null`                                                                                               |

`between` takes `[low, high]` inclusive; `is_null` takes `true` or `false`. Values are data: they are parameterized, never interpreted, and `%` is a literal.

## Errors

A bad request is HTTP 400 keyed by the path of the offending part, for example `{"filter.and[1].op": ["status field 'status' does not support 'contains'; use eq, ne, in, is_null."]}`; `sort`, `columns`, `limit` and `offset` are keyed by their own names. An unknown entity is 404, a role the entity does not allow is 403, another workspace's event is 404.

## Registering an entity

In an `entities` module of your app (imported automatically), call `core.entities.register(Entity(...))` with a key, label, the roles that may query it, `base(event, user)` returning the rows that person may see for the event (the only place visibility is decided), the `Field`s (key, type, ORM column of a stored value, label, sortable, filterable, choices, default column) and a default sort. Only registered fields and operators are reachable; nothing else from the client reaches the ORM. Add a conformance case if the field set is unusual (`tests/integration/test_entity_query.py` already proves every registered field filters and sorts).

The web side is `src/web/lib/entityQuery.ts` (types, canonical filter text, URLs, `useEntityCatalogue`, `useEntityPage`) and `FilterBuilder` for building a filter from the catalogue.

## Compatibility

Existing list endpoints and their parameters (for example `applications/?status=`) are unchanged; they can adopt the entity query when they are next touched.
