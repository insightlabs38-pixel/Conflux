# PD-F002 — Feature depth should compound through shared primitives

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §2  
**Queue batches:** PD-F002-B01, PD-F002-B02, PD-F002-B03

## Completion interpretation

This specification is the canonical depth contract for §2. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Shared primitives are platform contracts, not helper functions. Each must define canonical state, lifecycle, authorization, idempotency/concurrency behavior, error shape, extension boundary and migration policy before dependents rely on it.
- Dependents must import/reuse these primitives rather than recreating similar local abstractions.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `PREVIEW_CONTEXT`
- `QUERY`
- `SCHEMA_EDITOR`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
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

Before adding hundreds of bespoke screens, Conflux should build reusable primitives that make the next 100 features cheaper:

- Universal entity query/filter engine.
- Saved views and sharable view URLs.
- Configurable dense data-grid primitive.
- Bulk-operation planner with dry-run, impact preview, execution receipt, retry and rollback/compensation semantics where possible.
- Generic async-job/task model with progress, cancellation, logs, artifacts and durable results.
- Generic approval/gate model.
- Generic comments/notes/mentions/thread model with explicit visibility.
- Generic event timeline/scheduling primitive.
- Generic schema-driven form/config editor.
- Generic rich technical content renderer/editor.
- Generic file/artifact preview pipeline.
- Generic notification/subscription preference model.
- Generic version/diff model for mutable configuration and content.
- Generic policy/explanation model.
- Generic audit provenance envelope.
- Generic extension manifest/capability model.
- Generic “preview as role / as of time / as frozen version” infrastructure.

## Batch scope

### PD-F002-B01 — Feature depth should compound through shared primitives — Universal entity query/filter engine → Generic event timeline/scheduling primi…

- Shared primitive: Universal entity query/filter engine
- Shared primitive: Saved views and sharable view URLs
- Shared primitive: Configurable dense data-grid primitive
- Shared primitive: Bulk-operation planner with dry-run, impact preview, execution receipt, retry and rollback/compensation semanti…
- Shared primitive: Generic async-job/task model with progress, cancellation, logs, artifacts and durable results
- Shared primitive: Generic approval/gate model
- Shared primitive: Generic comments/notes/mentions/thread model with explicit visibility
- Shared primitive: Generic event timeline/scheduling primitive

### PD-F002-B02 — Feature depth should compound through shared primitives — Generic schema-driven form/config editor → Generic extension manifest/capability m…

- Shared primitive: Generic schema-driven form/config editor
- Shared primitive: Generic rich technical content renderer/editor
- Shared primitive: Generic file/artifact preview pipeline
- Shared primitive: Generic notification/subscription preference model
- Shared primitive: Generic version/diff model for mutable configuration and content
- Shared primitive: Generic policy/explanation model
- Shared primitive: Generic audit provenance envelope
- Shared primitive: Generic extension manifest/capability model

### PD-F002-B03 — Feature depth should compound through shared primitives — Generic “preview as role / as of time / as frozen version” infra…

- Shared primitive: Generic “preview as role / as of time / as frozen version” infrastructure

