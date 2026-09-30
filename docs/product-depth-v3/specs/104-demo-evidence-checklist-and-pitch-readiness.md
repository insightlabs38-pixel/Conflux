# PD-S104 — Demo evidence checklist and pitch readiness

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §104  
**Queue batches:** PD-S104-B01, PD-S104-B02

## Completion interpretation

This specification is the canonical depth contract for §104. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `AUDIT_PROVENANCE`
- `PREVIEW_CONTEXT`
- `QUERY`
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
| `archive` | required |
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

The project authoring system can help teams present the work judges actually need to see.

- BASE — event-defined required demo duration/format.
- BASE — upload/link video.
- BASE — project preflight says whether demo evidence is present.
- ADV — checklist from judging criteria: core flow, technical architecture, limitation disclosure, sponsor requirement.
- ADV — video duration validation.
- ADV — transcript/captions supplied by participant/provider where available.
- ADV — judge can mark demo artifact reviewed.
- ADV — exact demo URL/version frozen with submission.
- EXPERT — participant “judge preview” mode that shows exactly what a judge sees.

**Why include:** MLH recommends short demo videos specifically to improve judging; recent participant complaints show why evidence visibility matters.

## Batch scope

### PD-S104-B01 — Demo evidence checklist and pitch readiness — event-defined required demo duration/fo… → exact demo URL/version frozen with subm…

- event-defined required demo duration/format
- upload/link video
- project preflight says whether demo evidence is present
- checklist from judging criteria: core flow, technical architecture, limitation disclosure, sponsor requirement
- video duration validation
- transcript/captions supplied by participant/provider where available
- judge can mark demo artifact reviewed
- exact demo URL/version frozen with submission

### PD-S104-B02 — Demo evidence checklist and pitch readiness — participant “judge preview” mode that shows exactly what a judge…

- participant “judge preview” mode that shows exactly what a judge sees

