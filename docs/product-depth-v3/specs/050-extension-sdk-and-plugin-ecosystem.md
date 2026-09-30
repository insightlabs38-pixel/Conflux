# PD-S050 — Extension SDK and plugin ecosystem

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §50  
**Queue batches:** PD-S050-B01, PD-S050-B02, PD-S050-B03, PD-S050-B04

## Completion interpretation

This specification is the canonical depth contract for §50. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Extensions declare capabilities and compatibility through the canonical extension manifest. Extensions do not bypass authorization, audit, portability or upgrade boundaries.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
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
| `archive` | not_required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/event-builder`
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

The extension SDK can make extreme customization sustainable, but only if it is declarative-first and capability-scoped.
- BASE — first-party install ships fully useful with no extensions.
- PROG — extension manifest with name/version/compatibility/capabilities.
- PROG — explicit extension points, not arbitrary imports into internal modules.
- PROG — artifact renderer extension.
- PROG — preflight/checker extension.
- PROG — import/export adapter extension.
- PROG — page block extension.
- PROG — form field extension.
- PROG — judging strategy/diagnostic extension.
- PROG — integration/provider extension.
- PROG — notification channel extension.
- PROG — analytics widget extension.
- PROG — custom Event-as-Code resource/config schema.
- PROG — schema-generated fallback UI for extension config.
- PROG — optional custom React UI under a restricted stable component/API surface.
- ADV — per-event enable/disable.
- ADV — extension settings versioning and migration.
- ADV — extension permission/capability declaration.
- ADV — extension health/status surface.
- EXPERT — sandbox or process isolation for untrusted executable extensions where feasible.
- EXPERT — declarative extension class that executes no arbitrary code.
- EXPERT — trusted/restricted mode for installations/extensions.
- EXPERT — signed packages/checksums.
- EXPERT — extension conformance test kit.
- EXPERT — compatibility matrix against Conflux releases.
- EXPERT — reference extension for each supported family.
- EXPERT — extension marketplace/catalog can be optional and decentralized.

## Batch scope

### PD-S050-B01 — Extension SDK and plugin ecosystem — first-party install ships fully useful… → form field extension

- first-party install ships fully useful with no extensions
- extension manifest with name/version/compatibility/capabilities
- explicit extension points, not arbitrary imports into internal modules
- artifact renderer extension
- preflight/checker extension
- import/export adapter extension
- page block extension
- form field extension

### PD-S050-B02 — Extension SDK and plugin ecosystem — judging strategy/diagnostic extension → per-event enable/disable

- judging strategy/diagnostic extension
- integration/provider extension
- notification channel extension
- analytics widget extension
- custom Event-as-Code resource/config schema
- schema-generated fallback UI for extension config
- optional custom React UI under a restricted stable component/API surface
- per-event enable/disable

### PD-S050-B03 — Extension SDK and plugin ecosystem — extension settings versioning and migra… → extension conformance test kit

- extension settings versioning and migration
- extension permission/capability declaration
- extension health/status surface
- sandbox or process isolation for untrusted executable extensions where feasible
- declarative extension class that executes no arbitrary code
- trusted/restricted mode for installations/extensions
- signed packages/checksums
- extension conformance test kit

### PD-S050-B04 — Extension SDK and plugin ecosystem — compatibility matrix against Conflux re… → extension marketplace/catalog can be op…

- compatibility matrix against Conflux releases
- reference extension for each supported family
- extension marketplace/catalog can be optional and decentralized

