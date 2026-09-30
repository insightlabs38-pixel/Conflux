# PD-S111 — Searchable event knowledge base / FAQ with operational linkage

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §111  
**Queue batches:** PD-S111-B01, PD-S111-B02

## Completion interpretation

This specification is the canonical depth contract for §111. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
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
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/participant-my-event`
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

Conflux already has public Q&A/resources; connect them more tightly to operations.

- BASE — searchable FAQ.
- BASE — organizer-authored canonical answer.
- BASE — public/private audience.
- ADV — help-desk response can link/promote an answer.
- ADV — repeated help requests suggest FAQ gap.
- ADV — sponsor challenge FAQ belongs to sponsor context.
- ADV — rules FAQ links to exact rule.
- ADV — version/update timestamp.
- ADV — participant sees relevant FAQs based on current workflow.
- EXPERT — semantic search can be optional, with deterministic full-text search remaining baseline.

**Why include:** Reduces organizer support load without building a chatbot as the primary answer surface.

## Batch scope

### PD-S111-B01 — Searchable event knowledge base / FAQ with operational linkage — searchable FAQ → version/update timestamp

- searchable FAQ
- organizer-authored canonical answer
- public/private audience
- help-desk response can link/promote an answer
- repeated help requests suggest FAQ gap
- sponsor challenge FAQ belongs to sponsor context
- rules FAQ links to exact rule
- version/update timestamp

### PD-S111-B02 — Searchable event knowledge base / FAQ with operational linkage — participant sees relevant FAQs based on… → semantic search can be optional, with d…

- participant sees relevant FAQs based on current workflow
- semantic search can be optional, with deterministic full-text search remaining baseline

