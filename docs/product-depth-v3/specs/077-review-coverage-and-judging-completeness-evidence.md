# PD-S077 — Review coverage and judging-completeness evidence

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §77  
**Queue batches:** PD-S077-B01, PD-S077-B02

## Completion interpretation

This specification is the canonical depth contract for §77. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Coverage/completeness tracks official review obligations without invasive judge surveillance. Participant-facing evidence is bounded to configured transparency.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `TIMELINE`

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
| `analytics` | required |
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

This is a strong trust feature with a clear use.

For organizers:

- BASE — every project shows required reviews vs completed reviews.
- BASE — every ballot shows complete/incomplete without exposing peer scores to judges.
- BASE — missing rubric criteria highlighted.
- BASE — project with zero completed reviews is impossible to overlook.
- ADV — required demo/evidence checklist marked reviewed.
- ADV — stale/in-progress ballot detection.
- ADV — judge no-show/dropout warnings.
- ADV — deadline projection from current completion rate.
- ADV — auto-suggest rebalancing when coverage is at risk.
- ADV — “unreviewed for X minutes” operations view.
- ADV — finalist cannot silently advance while required coverage is missing unless an authorized override is recorded.
- EXPERT — evidence graph showing which independent completed reviews support each official ranking/award.

For participants, optionally after judging:

- BASE — show number of completed official reviews.
- ADV — show whether required demo/artifact evidence was included in the official frozen review package.
- ADV — release rubric feedback according to event policy.
- ADV — never expose private judge activity timelines or identities unless the event explicitly publishes them.

**Why include:** It directly addresses a common participant trust complaint without adding performative cryptography.

## Batch scope

### PD-S077-B01 — Review coverage and judging-completeness evidence — every project shows required reviews vs… → deadline projection from current comple…

- every project shows required reviews vs completed reviews
- every ballot shows complete/incomplete without exposing peer scores to judges
- missing rubric criteria highlighted
- project with zero completed reviews is impossible to overlook
- required demo/evidence checklist marked reviewed
- stale/in-progress ballot detection
- judge no-show/dropout warnings
- deadline projection from current completion rate

### PD-S077-B02 — Review coverage and judging-completeness evidence — auto-suggest rebalancing when coverage… → never expose private judge activity tim…

- auto-suggest rebalancing when coverage is at risk
- unreviewed for X minutes” operations view
- finalist cannot silently advance while required coverage is missing unless an authorized override is recorded
- evidence graph showing which independent completed reviews support each official ranking/award
- show number of completed official reviews
- show whether required demo/artifact evidence was included in the official frozen review package
- release rubric feedback according to event policy
- never expose private judge activity timelines or identities unless the event explicitly publishes them

