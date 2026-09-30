# PD-S041 — Search, query language and saved views

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §41  
**Queue batches:** PD-S041-B01, PD-S041-B02, PD-S041-B03

## Completion interpretation

This specification is the canonical depth contract for §41. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Section 41 extends the canonical QUERY/SAVED_VIEWS/DATA_GRID primitives from foundation; it must not introduce a second query language or saved-view representation.

## Canonical primitive reuse

- `ASYNC_JOB`
- `BULK_PLAN`
- `DATA_GRID`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SAVED_VIEWS`
- `SCHEMA_EDITOR`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | required |
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

A universal query engine can unify organizer tables, analytics, exports, communications audiences, bulk ops, CLI and MCP.
- BASE — simple search box on every major collection.
- BASE — visual filter builder.
- ADV — nested boolean conditions.
- ADV — typed operators by field.
- ADV — relative time operators.
- ADV — relation filters: team has member, project has finding, judge has conflict.
- ADV — aggregate predicates where safe: review count < 2.
- ADV — named saved views.
- ADV — share/favorite/pin.
- ADV — dynamic columns.
- ADV — query diagnostics when a filter is expensive.
- EXPERT — text query syntax with autocomplete.
- EXPERT — formulas/computed fields.
- EXPERT — permission-safe cross-domain queries.
- EXPERT — query plan/cost guardrails.
- PROG — same query AST used by UI/API/CLI/MCP.
- PROG — saved query can drive communication audience, export, dashboard widget or bulk operation.

## Batch scope

### PD-S041-B01 — Search, query language and saved views — simple search box on every major collec… → named saved views

- simple search box on every major collection
- visual filter builder
- nested boolean conditions
- typed operators by field
- relative time operators
- relation filters: team has member, project has finding, judge has conflict
- aggregate predicates where safe: review count < 2
- named saved views

### PD-S041-B02 — Search, query language and saved views — share/favorite/pin → same query AST used by UI/API/CLI/MCP

- share/favorite/pin
- dynamic columns
- query diagnostics when a filter is expensive
- text query syntax with autocomplete
- formulas/computed fields
- permission-safe cross-domain queries
- query plan/cost guardrails
- same query AST used by UI/API/CLI/MCP

### PD-S041-B03 — Search, query language and saved views — saved query can drive communication audience, export, dashboard…

- saved query can drive communication audience, export, dashboard widget or bulk operation

