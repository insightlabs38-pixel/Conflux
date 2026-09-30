# PD-S074 — Staff, judge, mentor, speaker and volunteer recruitment/onboarding

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §74  
**Queue batches:** PD-S074-B01, PD-S074-B02, PD-S074-B03

## Completion interpretation

This specification is the canonical depth contract for §74. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Recruitment/invitation state feeds readiness and staffing; role activation remains a canonical authorization transition.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `BULK_PLAN`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
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
| `archive` | not_required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/onsite-mobile`
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

Conflux has role workspaces, but there is value in the workflow *before* someone becomes an active staff member.

- BASE — public/private interest form for judge/mentor/volunteer/speaker.
- BASE — invitation and acceptance/decline.
- BASE — role-specific onboarding checklist.
- BASE — event date/time/location expectations.
- BASE — Code of Conduct/rules acknowledgement.
- ADV — availability windows.
- ADV — expertise/track preferences.
- ADV — role capacity/needed-count target.
- ADV — organizer review/approval.
- ADV — bulk invite.
- ADV — reminder sequence for unconfirmed invitees.
- ADV — waitlist/backup pool.
- ADV — previous-event role history.
- ADV — “confirmed / tentative / declined / no response” dashboard.
- EXPERT — reusable cross-event staff directory.
- EXPERT — suggested judge/mentor candidates from prior events, never automatic outreach.
- PROG — invitation state should feed staffing and judging-readiness calculations.

**Why include:** Judge/mentor recruitment happens before the sophisticated assignment features can help.

## Batch scope

### PD-S074-B01 — Staff, judge, mentor, speaker and volunteer recruitment/onboarding — public/private interest form for judge/… → role capacity/needed-count target

- public/private interest form for judge/mentor/volunteer/speaker
- invitation and acceptance/decline
- role-specific onboarding checklist
- event date/time/location expectations
- Code of Conduct/rules acknowledgement
- availability windows
- expertise/track preferences
- role capacity/needed-count target

### PD-S074-B02 — Staff, judge, mentor, speaker and volunteer recruitment/onboarding — organizer review/approval → suggested judge/mentor candidates from…

- organizer review/approval
- bulk invite
- reminder sequence for unconfirmed invitees
- waitlist/backup pool
- previous-event role history
- confirmed / tentative / declined / no response” dashboard
- reusable cross-event staff directory
- suggested judge/mentor candidates from prior events, never automatic outreach

### PD-S074-B03 — Staff, judge, mentor, speaker and volunteer recruitment/onboarding — invitation state should feed staffing and judging-readiness calc…

- invitation state should feed staffing and judging-readiness calculations

