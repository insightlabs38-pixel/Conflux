# PD-S068 — Developer experience, docs and reference environments

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §68  
**Queue batches:** PD-S068-B01, PD-S068-B02

## Completion interpretation

This specification is the canonical depth contract for §68. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `EXTENSION_MANIFEST`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TYPED_CLIENT`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | not_required |
| `sdk` | required |
| `cli` | required |
| `mcp` | not_required |
| `event_as_code` | required |
| `audit` | not_required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | required |
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

If Conflux becomes extremely deep, documentation must become part of the architecture.
- BASE — quickstart that genuinely works.
- BASE — operator guide organized by lifecycle.
- BASE — participant/judge guides generated from enabled features where possible.
- ADV — API recipes.
- ADV — Event-as-Code examples.
- ADV — extension SDK reference examples.
- ADV — architecture decision records.
- ADV — compatibility/support matrix.
- ADV — interactive demo event.
- ADV — documented domain glossary.
- ADV — “how this feature composes with…” links.
- ADV — generated schema docs from source metadata.
- EXPERT — local docs search.
- EXPERT — runnable tutorial fixtures.
- EXPERT — upgrade cookbook with semantic config/API changes.
- PROG — examples validated in CI so docs do not rot.

## Batch scope

### PD-S068-B01 — Developer experience, docs and reference environments — quickstart that genuinely works → compatibility/support matrix

- quickstart that genuinely works
- operator guide organized by lifecycle
- participant/judge guides generated from enabled features where possible
- API recipes
- Event-as-Code examples
- extension SDK reference examples
- architecture decision records
- compatibility/support matrix

### PD-S068-B02 — Developer experience, docs and reference environments — interactive demo event → examples validated in CI so docs do not…

- interactive demo event
- documented domain glossary
- how this feature composes with…” links
- generated schema docs from source metadata
- local docs search
- runnable tutorial fixtures
- upgrade cookbook with semantic config/API changes
- examples validated in CI so docs do not rot

