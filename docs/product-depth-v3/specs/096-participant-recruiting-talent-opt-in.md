# PD-S096 — Participant recruiting / talent opt-in

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §96  
**Queue batches:** PD-S096-B01, PD-S096-B02

## Completion interpretation

This specification is the canonical depth contract for §96. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Talent discovery is participant opt-in with field-level consent; no automatic candidate-quality scoring from judging and no full ATS.

## Canonical primitive reuse

- `ASYNC_JOB`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`

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
- No full ATS and no automatic candidate-quality score derived from judging.

## Product requirements from research

This can be useful if participant-controlled.

- BASE — optional “open to opportunities” profile setting.
- BASE — participants choose which profile fields can be shared.
- BASE — event-specific consent.
- ADV — sponsor/recruiter can filter only consenting participants.
- ADV — bookmarks/shortlists.
- ADV — participant can see which organizations received their profile if the event chooses transparent sharing.
- ADV — follow-up status is optional and private to authorized recruiting staff.
- ADV — opt-out/revoke where legally feasible.
- EXPERT — export to external ATS/CRM.
- DO NOT BUILD — full applicant tracking system.
- DO NOT BUILD — automatic “candidate quality” scoring from hackathon judging results.

**Why include:** Recruiting is a common sponsor/organizer goal, but it should not compromise the competition experience.

## Batch scope

### PD-S096-B01 — Participant recruiting / talent opt-in — optional “open to opportunities” profil… → opt-out/revoke where legally feasible

- optional “open to opportunities” profile setting
- participants choose which profile fields can be shared
- event-specific consent
- sponsor/recruiter can filter only consenting participants
- bookmarks/shortlists
- participant can see which organizations received their profile if the event chooses transparent sharing
- follow-up status is optional and private to authorized recruiting staff
- opt-out/revoke where legally feasible

### PD-S096-B02 — Participant recruiting / talent opt-in — export to external ATS/CRM

- export to external ATS/CRM

