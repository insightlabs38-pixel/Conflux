# PD-F006 — Universal data-grid and saved-view system

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §6  
**Queue batches:** PD-F006-B01, PD-F006-B02, PD-F006-B03, PD-F006-B04, PD-F006-B05

## Completion interpretation

This specification is the canonical depth contract for §6. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Data grid, saved views and query/filtering must share one typed query model. URL state, saved state, bulk target selection, exports, CLI queries and MCP references must not fork into incompatible filter syntaxes.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `BULK_PLAN`
- `DATA_GRID`
- `PREVIEW_CONTEXT`
- `QUERY`
- `ROUTER`
- `SAVED_VIEWS`
- `SCHEMA_EDITOR`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/organizer-data-surface`
- `design/state-matrix`

These references must resolve to approved local design artifacts before UI-facing tasks close.

## Minimum verification contract

For the subsystem as a whole:
- realistic happy-path data;
- malformed/boundary behavior with useful diagnostics;
- authorization/visibility boundaries;
- lifecycle and migration/compatibility behavior;
- retry/idempotency/concurrency for shared-state mutations;
- required browser states for UI-facing flows;
- no regression of canonical existing behavior;
- exact commands/results recorded in receipts.

## Non-goals / restraint

- No duplicate source of truth solely for a new surface.
- No redundant hash/signature/proof layer unless it enables a real portability, offline-verification or external-trust workflow.
- No LLM/AI decision authority for deterministic official state such as scores, permissions, deadlines, policy or winner selection.
- No participant surveillance or engagement gamification without a concrete event purpose.
- No replacement of a mature generic external product category when a bounded integration solves the event-specific need.

## Product requirements from research

This is one of the highest-leverage UI primitives.

- BASE: sortable columns.
- BASE: search.
- BASE: structured filters.
- BASE: row selection.
- BASE: bulk-action bar.
- BASE: column show/hide.
- BASE: pagination or virtualized windowing depending on dataset.
- BASE: sticky header where appropriate.
- BASE: responsive fallback for narrow screens.
- ADV: nested AND/OR filter groups.
- ADV: filter operators appropriate to data type.
- ADV: saved private views.
- ADV: shared organizer views.
- ADV: favorite/pin views.
- ADV: URL-encoded shareable transient views.
- ADV: group/subgroup.
- ADV: list / board / matrix / calendar where semantically valid.
- ADV: aggregate footer values.
- ADV: computed columns.
- ADV: inline editing with validation.
- ADV: keyboard row navigation and range selection.
- ADV: split-pane inspection.
- ADV: “only changed since…” filter.
- ADV: view templates.
- EXPERT: text query language equivalent to UI filters.
- EXPERT: organization-managed canonical views.
- EXPERT: permission-aware columns/filters.
- EXPERT: export the current exact filtered view.
- EXPERT: subscribe to view changes.
- PROG: saved-view schema is accessible over API.
- PROG: CLI can run the same query.
- PROG: MCP can reference a saved view rather than re-send a giant filter.
- PROG: bulk operations can consume a saved view with a frozen membership snapshot.

## Batch scope

### PD-F006-B01 — Universal data-grid and saved-view system — sortable columns → sticky header where appropriate

- sortable columns
- search
- structured filters
- row selection
- bulk-action bar
- column show/hide
- pagination or virtualized windowing depending on dataset
- sticky header where appropriate

### PD-F006-B02 — Universal data-grid and saved-view system — responsive fallback for narrow screens → group/subgroup

- responsive fallback for narrow screens
- nested AND/OR filter groups
- filter operators appropriate to data type
- saved private views
- shared organizer views
- favorite/pin views
- URL-encoded shareable transient views
- group/subgroup

### PD-F006-B03 — Universal data-grid and saved-view system — list / board / matrix / calendar where… → view templates

- list / board / matrix / calendar where semantically valid
- aggregate footer values
- computed columns
- inline editing with validation
- keyboard row navigation and range selection
- split-pane inspection
- only changed since…” filter
- view templates

### PD-F006-B04 — Universal data-grid and saved-view system — text query language equivalent to UI fi… → MCP can reference a saved view rather t…

- text query language equivalent to UI filters
- organization-managed canonical views
- permission-aware columns/filters
- export the current exact filtered view
- subscribe to view changes
- saved-view schema is accessible over API
- CLI can run the same query
- MCP can reference a saved view rather than re-send a giant filter

### PD-F006-B05 — Universal data-grid and saved-view system — bulk operations can consume a saved view with a frozen membershi…

- bulk operations can consume a saved view with a frozen membership snapshot


## PD-F006-B01 canonical contract

Written by PD-F006-B01-T00 against the approved design (`design/organizer-data-surface`, `design/state-matrix`; boards Data-Surface, Data-Filters, Resp-1024, Wide-1920) and the code as it stands on 2026-10-08. Baseline evidence: `tests/integration/test_entity_query.py` and `test_saved_views.py` (46 passed) and the web suite (827 passed). The owned paths named in the queue (`src/api/search`, `src/web/components/data-grid`, `src/web/features/search`) do not exist; the real owners are listed below and are the paths B01 tasks change.

### What exists (reuse, do not rebuild)

- **Query engine (QUERY).** `src/api/core/query.py`: a versioned JSON filter tree (AND/OR to depth 4, 20 predicates, `in` up to 50), up to 3 sort keys with a `pk` tiebreak, a column list, compiled to ORM from registered fields only, refusals keyed by path (`filter.and[1].op`). `core/entities.py` registers `Entity` and `Field`; `projects` and `events` (applications) are registered. `GET .../events/{e}/entities/` is the catalogue and `.../entities/{key}/` the page (`limit` 1..100, `offset`, `total` counted). Verified by `features_search.py` (searchable and filterable fields are the registered ones).
- **Saved views (SAVED_VIEWS).** `core/saved_views.py` and `SavedView` (`query` JSON: filter, sort, columns, density; `version`; private or organizers); a view stores a definition, never rows, and runs under the viewer's authorization.
- **Grid (DATA_GRID).** `components/DataGrid.tsx` (native table: caption, `aria-sort`, sticky header, per-page selection, empty/loading/error states), `EntityGrid.tsx` (catalogue-driven columns, sort and page as URL panel params, remembered columns, live mode, inspector, selection commands), `FilterBuilder.tsx`, `ViewBar.tsx`, `lib/entityQuery.ts`, `lib/savedViews.ts`.
- **Bulk (BULK_PLAN).** `BulkPlanner.tsx` previews, applies and receipts an operation of at most 100 explicit targets; `ProjectsGrid` is its only bulk bar today and is ad hoc markup.
- **Missing.** Free-text search on the entity query; a shared bulk-action bar; a select-all-on-page control; page-size and range controls; any CLI command or MCP tool that runs an entity query.

### Decisions (conservative defaults, reversible)

1. **One query model, extended once.** Search, sort, filter, columns and paging stay parameters of the one entity query. B01 adds exactly one: `search`. No second filter syntax, no client-side filtering of rows, no per-grid query parameters.
2. **Search (T02).** `Entity.search_fields` (a tuple of registered `TEXT` field keys, optional; an entity without it has no search box). `search` is split into at most 5 terms of at most 200 characters; every term must match (`icontains`) at least one search field; the result is ANDed with the filter. Terms under 2 characters are refused with a path-keyed 400. It is part of the typed definition: a saved view may carry `search` (optional additive key; views without it read as before, `version` unchanged). Search text is typed text, so it is **transient state**: held in the grid, never in the URL or device storage (spec 005); sharing a search means saving a view.
3. **Sort (T01).** Header activation cycles ascending, descending, off; shift-activate adds a secondary key up to 3 (the engine's limit). `aria-sort` and an announced change. Order is always deterministic (`pk` tiebreak); nulls sort last in both directions. Sort stays `sort_<entity>` in the URL.
4. **Filters (T03).** B01 closes flat conditions joined by AND, typed by field with the operators the catalogue lists, with the server's path-keyed diagnostic shown beside the condition it names and an equivalent read-only query line. Nested groups and richer per-type operators are B02. The builder emits the same tree the engine reads; nothing is translated client-side.
5. **Selection (T04).** Selection is ids on the current page: header tri-state select-all-on-page, announced count ("3 selected"), cleared by page, filter or search change, and capped at the planner's 100 targets with a stated reason. "Select all N matching" is a frozen membership snapshot and belongs to B05; B01 does not fake it with a client loop. Range selection is B03.
6. **Bulk bar (T05).** One `BulkBar` component (design: exactly one primary action, at most 4 actions plus More, selection count, Clear). A list declares its actions; each opens `BulkPlanner` (preview, receipt). `ProjectsGrid` is migrated onto it. A bulk action never mutates from the bar itself.
7. **Columns (T06).** Existing picker and remembered choice are completed: at least one column, keyboard operable, reset, saved with a view, disclosed under the grid tools on narrow screens. Column order and resize are not in scope (design limitation).
8. **Paging, no client virtualization (T07).** Server offset pagination stays canonical (limit at most 100, deterministic order, counted `total`). B01 adds a page-size choice (25, 50, 100), range text ("26 to 50 of 5,012"), first, previous, next, last and keeps `page_<entity>` in the URL. Client row virtualization is deliberately not built: a page is at most 100 native table rows, and windowing would break table semantics, find-in-page and `aria-rowcount`. The design's "row window" cue is the range text. If the 5,012-row fixture shows the counted query or render exceeding 300 ms at the largest page, record a performance escalation instead of adding a second paging model.
9. **Sticky header (T08).** The header is sticky inside the grid's own scroll container when the table is taller than it, with the inspector docked and at 1440, 1100 and 390; never sticky where the phone layout becomes a row list (B02). The existing sticky rule is verified and kept, not rewritten.
10. **CLI and MCP (surface matrix).** B01 closes the read path only: `conflux entities query` (SDK CLI) and an MCP read tool `query_entity` call the same route with the same parameters (`filter` JSON, `sort`, `columns`, `search`, `limit`, `offset`), under the credential's own authority, with feature claims and tests per `features_cli.py` and `features_mcp.py`. Saved-view references, a text query language and exports remain B04. No new route.
11. **Audit.** No new write. Saved-view create, update and delete are already audited through `record_mutation`; a bulk apply is already receipted and audited by the planner; reads of the entity query are not audited today and stay so.

### Invariants

- The server compiles every query from registered fields; a client string never becomes a lookup, relation or SQL. Authorization is the entity's `base(event, user)` and its roles; the grid, CLI and MCP see the same rows.
- A saved view stores a definition, never rows or ids; running it re-authorizes.
- One source of truth per concern: query in `core/query.py`, view definitions in `core/saved_views.py`, remembered preferences in `shellPreferences`, selection in `EntityGrid` state published through `lib/selection.ts`, bulk targets through `BulkPlanner`.
- Participant-supplied cell values are text, never markup.
- Defaults unchanged: a grid with no search field, no selection and default columns looks and behaves as today.

### Forbidden duplicates

A second filter syntax or parser; client-side filtering, sorting or paging of rows; a grid-local search implementation; a bulk bar built by hand in a feature; a second saved-view store; a virtualization layer beside server paging; a CLI or MCP query that is not the entity route; search text in a URL or in storage.

### Migration and compatibility

No database migration. The query API gains one optional parameter (`search`) and entities an optional registration field; OpenAPI and both SDKs are regenerated and checked (`make verify-fast`). `normalize` in `saved_views.py` accepts `search` as an optional key; stored views without it round-trip unchanged and a view with it saved by a newer build read by an older build is refused with the existing "Unknown keys" 400 only if the older build runs against the same database, which the deployment order (API before web) prevents. Existing `sort_<entity>`, `page_<entity>`, `row_<entity>`, `view_<entity>` params keep their meaning.

### Cross-surface applicability

web required (grid, bulk bar, search, paging); api required (`search`, `Entity.search_fields`); sdk not required but regenerated; cli and mcp required (read path above); audit required (confirmation above); search required (this batch); docs required; event_as_code, webhook, archive, analytics not required.

### Task boundaries

T01 sort headers; T02 `search` end to end (engine, saved definition, UI box, CLI and MCP parameter); T03 flat typed filters with diagnostics and query line; T04 selection and announcements; T05 `BulkBar` and the projects migration; T06 columns completion; T07 page size, range and navigation controls; T08 sticky header verification; T90 matrix; T91 CLI and MCP read tools, docs, surfaces. T02 changes the shared engine and runs first among the implementation tasks; the rest touch the web grid and are serialized on the `frontend` lock.

### Test strategy

Engine and API: pytest for search (terms, limits, multi-field OR, AND with filter, authorization, path-keyed errors), saved-view round trip with and without `search`. Web: vitest for sort cycle, selection rules and cap, bulk bar action limits, paging controls, search not in URL. Browser (desktop and mobile): `data-grid-*` specs on the seeded stack and an isolated fixture with 5,012 rows for paging and sticky header; axe on each state. Compatibility: the 46 existing query and saved-view tests stay green unchanged.

### As built (PD-F006-B01)

- All eleven decisions held. Search is `search` plus `Entity.search_fields`, in saved views only when used. Sort cycles and Shift adds keys, the address joins keys with a colon. Filters read back as a sentence and show the server's path-keyed message beside the condition, debounced. Selection is page-scoped, pruned and bounded; `BulkBar` is the one bar and `ProjectsGrid` uses it. Paging is server paging with `size_<entity>`, First, Last, Page X of Y and a past-the-end landing; no client virtualization, measured at 5,016 rows (API 31 to 43 ms, sort at 100 rows 89 ms).
- CLI `entities list|query` and MCP `query_entity` are thin read-only calls of the entity routes, recorded as outside the feature registry with reasons.
- Limitations carried: the phone's stacked rows have no header row, so multi-key sort and select-all-on-page are desktop gestures until B02; only the projects grid has a bulk action; select-all-matching (frozen snapshot) is B05.

### As built (PD-F006-B02)

- B02 has no T00; its decisions are in the receipts and QUESTIONS.md. Phone: the header is a bar above the row list, not hidden; 641 to 1023px keeps the select and name columns sticky. Filters: a recursive builder over the server tree (three group levels, twenty conditions), negations kept, operators worded and entered by type. Saved views: Reset, visibility line, Pinned group, conflict reload. Transient views: `f_<entity>`, structured values only, refused whole when it does not fit (numbers and dates count as structured - one function to tighten). Group and subgroup: `group` and `subgroup` return buckets with counts from the same filtered queryset, a bucket opens through the ordinary query, saved views may carry them.
- Limitations carried: selection, bulk and the inspector stay in the flat list; a count is the only aggregate; negations cannot be authored; pins are device-local; a second-organizer browser test needs a second organizer in the seed.

### Open questions (logged in QUESTIONS.md with the defaults above)

Search text transient rather than in the URL (P3); pagination without client virtualization (P2); CLI and MCP read path in B01 rather than B04 (P3).
