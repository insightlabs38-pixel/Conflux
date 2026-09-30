# PD-S012 — Registration, applications, admissions and waitlists

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §12  
**Queue batches:** PD-S012-B01, PD-S012-B02, PD-S012-B03

## Completion interpretation

This specification is the canonical depth contract for §12. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
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
| `analytics` | required |
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

A serious application subsystem can borrow from admissions/review systems while keeping the common “open registration” path trivial.
- BASE — open registration or approval-required registration.
- BASE — configurable registration window and capacity.
- BASE — draft application autosave.
- BASE — participant-facing status and next action.
- BASE — accepted/rejected/waitlisted/withdrawn/checked-in states.
- BASE — confirmation and RSVP workflow.
- ADV — multi-step application forms.
- ADV — conditional questions.
- ADV — reviewer queue with keyboard accept/reject/waitlist/undo.
- ADV — configurable reviewer rubric separate from project judging.
- ADV — blind application review.
- ADV — multiple admission reviewers with consensus/majority/manual decision policy.
- ADV — application comments and private reviewer notes.
- ADV — admission conflicts/recusal.
- ADV — waitlist rank/priority policies.
- ADV — automated waitlist promotion with capacity guardrails.
- ADV — per-cohort capacity targets and soft targets.
- ADV — application deduplication signals.
- ADV — document/file questions.
- ADV — participant correction/remediation request.
- EXPERT — staged admission workflow: screen → review → interview → decision.
- EXPERT — admissions calibration and inter-rater analysis.
- EXPERT — policy simulator for how a rule would affect current applicants.
- PROG — bulk admissions actions use dry-run and immutable decision receipts.

## Batch scope

### PD-S012-B01 — Registration, applications, admissions and waitlists — open registration or approval-required… → conditional questions

- open registration or approval-required registration
- configurable registration window and capacity
- draft application autosave
- participant-facing status and next action
- accepted/rejected/waitlisted/withdrawn/checked-in states
- confirmation and RSVP workflow
- multi-step application forms
- conditional questions

### PD-S012-B02 — Registration, applications, admissions and waitlists — reviewer queue with keyboard accept/rej… → automated waitlist promotion with capac…

- reviewer queue with keyboard accept/reject/waitlist/undo
- configurable reviewer rubric separate from project judging
- blind application review
- multiple admission reviewers with consensus/majority/manual decision policy
- application comments and private reviewer notes
- admission conflicts/recusal
- waitlist rank/priority policies
- automated waitlist promotion with capacity guardrails

### PD-S012-B03 — Registration, applications, admissions and waitlists — per-cohort capacity targets and soft ta… → bulk admissions actions use dry-run and…

- per-cohort capacity targets and soft targets
- application deduplication signals
- document/file questions
- participant correction/remediation request
- staged admission workflow: screen → review → interview → decision
- admissions calibration and inter-rater analysis
- policy simulator for how a rule would affect current applicants
- bulk admissions actions use dry-run and immutable decision receipts

