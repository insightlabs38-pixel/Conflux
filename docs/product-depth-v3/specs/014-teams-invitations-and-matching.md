# PD-S014 — Teams, invitations and matching

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §14  
**Queue batches:** PD-S014-B01, PD-S014-B02, PD-S014-B03

## Completion interpretation

This specification is the canonical depth contract for §14. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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

Team formation can be much deeper than a marketplace list.
- BASE — create/join/leave team within policy.
- BASE — invitation links and explicit invitations.
- BASE — team-size min/max validation.
- BASE — team readiness panel.
- BASE — teammate search by skills/interests.
- ADV — “looking for team” and “looking for members” structured profiles.
- ADV — desired skills vs offered skills.
- ADV — timezone/language/onsite-remote compatibility.
- ADV — project-interest tags.
- ADV — shortlist/bookmark candidates.
- ADV — match explanations based on organizer-visible deterministic features.
- ADV — recommendation tuning without exposing private scoring internals.
- ADV — team chat link/integration rather than forcing Conflux to become Slack.
- ADV — pre-event team matching sessions.
- ADV — organizer-assisted matching queue.
- ADV — team merge/split workflow with project/submission consequences previewed.
- EXPERT — optimization-based team formation with hard/soft constraints.
- EXPERT — diversity constraints only when explicitly configured and legally/ethically appropriate.
- EXPERT — stability analysis: who is unmatched and why.
- EXPERT — historical matching feedback to improve future matching rules.
- PROG — matching simulation endpoint and reproducible result seed.

## Batch scope

### PD-S014-B01 — Teams, invitations and matching — create/join/leave team within policy → timezone/language/onsite-remote compati…

- create/join/leave team within policy
- invitation links and explicit invitations
- team-size min/max validation
- team readiness panel
- teammate search by skills/interests
- looking for team” and “looking for members” structured profiles
- desired skills vs offered skills
- timezone/language/onsite-remote compatibility

### PD-S014-B02 — Teams, invitations and matching — project-interest tags → team merge/split workflow with project/…

- project-interest tags
- shortlist/bookmark candidates
- match explanations based on organizer-visible deterministic features
- recommendation tuning without exposing private scoring internals
- team chat link/integration rather than forcing Conflux to become Slack
- pre-event team matching sessions
- organizer-assisted matching queue
- team merge/split workflow with project/submission consequences previewed

### PD-S014-B03 — Teams, invitations and matching — optimization-based team formation with… → matching simulation endpoint and reprod…

- optimization-based team formation with hard/soft constraints
- diversity constraints only when explicitly configured and legally/ethically appropriate
- stability analysis: who is unmatched and why
- historical matching feedback to improve future matching rules
- matching simulation endpoint and reproducible result seed

