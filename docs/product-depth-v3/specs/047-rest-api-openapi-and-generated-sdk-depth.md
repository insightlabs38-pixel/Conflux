# PD-S047 — REST API, OpenAPI and generated SDK depth

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §47  
**Queue batches:** PD-S047-B01, PD-S047-B02

## Completion interpretation

This specification is the canonical depth contract for §47. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `BULK_PLAN`
- `DATA_GRID`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TYPED_CLIENT`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | required |
| `sdk` | required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- No dedicated visual reference is required by default. Any UI introduced still follows the global Conflux v3 design system.

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

The API is already a real product surface. It should become difficult for the UI and automation layers to drift away from it.
- BASE/PROG — consistent pagination/error/idempotency conventions.
- PROG — generated TypeScript/Python SDKs remain contract-tested.
- PROG — operation IDs designed as stable developer-facing names.
- PROG — full schema examples.
- PROG — conditional request/ETag support on high-contention configuration where useful.
- PROG — idempotency keys for mutation classes vulnerable to retries.
- PROG — consistent async-job response shape.
- PROG — batch read endpoints where latency meaningfully improves.
- PROG — bulk operations through explicit plan/apply endpoints.
- PROG — versioned webhook event schemas.
- PROG — deprecation metadata and migration guide.
- PROG — compatibility tests against previous supported API version.
- PROG — API explorer generated from actual schema plus domain examples.
- EXPERT — sparse fieldsets / includes only if justified by large operator clients.
- EXPERT — cursor pagination for very large mutable collections where offset becomes problematic.
- EXPERT — conditional streaming/export endpoints for large datasets.

## Batch scope

### PD-S047-B01 — REST API, OpenAPI and generated SDK depth — consistent pagination/error/idempotency… → batch read endpoints where latency mean…

- consistent pagination/error/idempotency conventions
- generated TypeScript/Python SDKs remain contract-tested
- operation IDs designed as stable developer-facing names
- full schema examples
- conditional request/ETag support on high-contention configuration where useful
- idempotency keys for mutation classes vulnerable to retries
- consistent async-job response shape
- batch read endpoints where latency meaningfully improves

### PD-S047-B02 — REST API, OpenAPI and generated SDK depth — bulk operations through explicit plan/a… → conditional streaming/export endpoints…

- bulk operations through explicit plan/apply endpoints
- versioned webhook event schemas
- deprecation metadata and migration guide
- compatibility tests against previous supported API version
- API explorer generated from actual schema plus domain examples
- sparse fieldsets / includes only if justified by large operator clients
- cursor pagination for very large mutable collections where offset becomes problematic
- conditional streaming/export endpoints for large datasets

