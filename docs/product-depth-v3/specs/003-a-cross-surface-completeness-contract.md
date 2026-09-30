# PD-F003 — A cross-surface completeness contract

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §3  
**Queue batches:** PD-F003-B01, PD-F003-B02, PD-F003-B03

## Completion interpretation

This specification is the canonical depth contract for §3. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TYPED_CLIENT`
- `VERSION_DIFF`

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
| `archive` | required |
| `analytics` | required |
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

For every important domain feature, consider whether it needs all of the following:

- Stable public identity and clear lifecycle.
- Backend validation and invariants.
- Authorization and scope rules.
- Audit events.
- Idempotency/concurrency semantics.
- REST representation.
- Generated SDK representation.
- Search/filter/index fields.
- Base UI.
- Advanced UI.
- Bulk-operation support.
- CLI inspect/action support when useful.
- MCP inspect/plan/action support when useful.
- Event-as-Code representation if it is configuration, not runtime participant data.
- Webhook/outbox events.
- Archive/import/export representation.
- Analytics dimensions.
- Retention/privacy semantics.
- Extension hooks.
- Version/migration behavior.
- Test-fixture/scenario support.

A feature is “deep” when these pieces compose naturally, not when it has a long settings page.

## Batch scope

### PD-F003-B01 — A cross-surface completeness contract — Cross-surface contract: Stable public i… → Cross-surface contract: Search/filter/i…

- Cross-surface contract: Stable public identity and clear lifecycle
- Cross-surface contract: Backend validation and invariants
- Cross-surface contract: Authorization and scope rules
- Cross-surface contract: Audit events
- Cross-surface contract: Idempotency/concurrency semantics
- Cross-surface contract: REST representation
- Cross-surface contract: Generated SDK representation
- Cross-surface contract: Search/filter/index fields

### PD-F003-B02 — A cross-surface completeness contract — Cross-surface contract: Base UI → Cross-surface contract: Archive/import/…

- Cross-surface contract: Base UI
- Cross-surface contract: Advanced UI
- Cross-surface contract: Bulk-operation support
- Cross-surface contract: CLI inspect/action support when useful
- Cross-surface contract: MCP inspect/plan/action support when useful
- Cross-surface contract: Event-as-Code representation if it is configuration, not runtime participant data
- Cross-surface contract: Webhook/outbox events
- Cross-surface contract: Archive/import/export representation

### PD-F003-B03 — A cross-surface completeness contract — Cross-surface contract: Analytics dimen… → Cross-surface contract: Test-fixture/sc…

- Cross-surface contract: Analytics dimensions
- Cross-surface contract: Retention/privacy semantics
- Cross-surface contract: Extension hooks
- Cross-surface contract: Version/migration behavior
- Cross-surface contract: Test-fixture/scenario support

