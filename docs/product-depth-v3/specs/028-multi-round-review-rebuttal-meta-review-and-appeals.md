# PD-S028 — Multi-round review, rebuttal, meta-review and appeals

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §28  
**Queue batches:** PD-S028-B01, PD-S028-B02

## Completion interpretation

This specification is the canonical depth contract for §28. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Review-stage visibility is explicit per stage. Rebuttal/meta-review/appeal state must not mutate original reviews or erase history.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
- `TIMELINE`
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
| `archive` | required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/judge-review`
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

Technical competitions can support conference-like workflows without forcing them on normal hackathons.
- BASE — multiple judging rounds/presets.
- ADV — different rubric and reviewer pool per round.
- ADV — soft deadline vs hard lock for judges.
- ADV — finalist advancement from round results.
- ADV — participant feedback release window.
- ADV — participant rebuttal/clarification window.
- ADV — judge response to rebuttal.
- ADV — meta-review / panel chair role.
- ADV — decision summary separate from raw reviews.
- ADV — appeal request with defined grounds and window.
- ADV — appeal reviewer isolated from original reviewer where configured.
- ADV — corrected decision version with audit trail.
- EXPERT — arbitrary review-stage template: review → rebuttal → meta-review → decision.
- EXPERT — stage-specific visibility matrix.
- EXPERT — ethics/safety review stage for events that need it.
- PROG — review-stage schema lives in the same stage graph rather than a second workflow engine.

## Batch scope

### PD-S028-B01 — Multi-round review, rebuttal, meta-review and appeals — multiple judging rounds/presets → meta-review / panel chair role

- multiple judging rounds/presets
- different rubric and reviewer pool per round
- soft deadline vs hard lock for judges
- finalist advancement from round results
- participant feedback release window
- participant rebuttal/clarification window
- judge response to rebuttal
- meta-review / panel chair role

### PD-S028-B02 — Multi-round review, rebuttal, meta-review and appeals — decision summary separate from raw revi… → review-stage schema lives in the same s…

- decision summary separate from raw reviews
- appeal request with defined grounds and window
- appeal reviewer isolated from original reviewer where configured
- corrected decision version with audit trail
- arbitrary review-stage template: review → rebuttal → meta-review → decision
- stage-specific visibility matrix
- ethics/safety review stage for events that need it
- review-stage schema lives in the same stage graph rather than a second workflow engine

