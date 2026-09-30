# PD-S084 — Minor/guardian forms and participant consent records

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §84  
**Queue batches:** PD-S084-B01, PD-S084-B02

## Completion interpretation

This specification is the canonical depth contract for §84. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Consent/guardian workflows track requirement/version/completion; use external e-signature providers rather than inventing legal-signature infrastructure.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`
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

Do not build a legal-document platform. Build a clean evidence/requirements workflow.

- BASE — organizer-defined required acknowledgement/consent documents.
- BASE — versioned text/PDF.
- BASE — participant acknowledgement timestamp and document version.
- ADV — guardian-required flag based on configured age rules.
- ADV — guardian contact and completion state.
- ADV — upload externally signed form where required.
- ADV — expiration/re-sign if the document changes materially.
- ADV — check-in blocks only when organizer explicitly configures the document as required.
- ADV — media/photo consent as a separate opt-in/out record.
- ADV — privacy notice acknowledgement.
- EXPERT — external e-signature provider integration instead of implementing legal signatures in core.

**Why include:** Minor forms and participant acknowledgements are common at student events; workflow state matters even when legal signing is external.

## Batch scope

### PD-S084-B01 — Minor/guardian forms and participant consent records — organizer-defined required acknowledgem… → check-in blocks only when organizer exp…

- organizer-defined required acknowledgement/consent documents
- versioned text/PDF
- participant acknowledgement timestamp and document version
- guardian-required flag based on configured age rules
- guardian contact and completion state
- upload externally signed form where required
- expiration/re-sign if the document changes materially
- check-in blocks only when organizer explicitly configures the document as required

### PD-S084-B02 — Minor/guardian forms and participant consent records — media/photo consent as a separate opt-i… → external e-signature provider integrati…

- media/photo consent as a separate opt-in/out record
- privacy notice acknowledgement
- external e-signature provider integration instead of implementing legal signatures in core

