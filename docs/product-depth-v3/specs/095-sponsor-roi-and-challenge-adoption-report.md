# PD-S095 — Sponsor ROI and challenge adoption report

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §95  
**Queue batches:** PD-S095-B01, PD-S095-B02

## Completion interpretation

This specification is the canonical depth contract for §95. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/event-builder`
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

A practical post-event artifact.

- BASE — challenge page views.
- BASE — challenge opt-ins.
- BASE — eligible/submitted projects.
- BASE — awarded projects.
- BASE — workshop attendance.
- ADV — resource link engagement.
- ADV — mentor/office-hours usage for sponsor challenge.
- ADV — project technologies used, based on participant-declared data.
- ADV — participant feedback about sponsor tools.
- ADV — sponsor feedback survey.
- ADV — public result/project links.
- ADV — configurable report branding/export.
- EXPERT — recruiting/product-adoption metrics only with participant consent and clear data provenance.
- DO NOT BUILD — invasive browser/user tracking merely to inflate sponsor metrics.

**Why include:** Current hackathon platforms explicitly market sponsor ROI; this makes sponsorship easier to renew.

## Batch scope

### PD-S095-B01 — Sponsor ROI and challenge adoption report — challenge page views → project technologies used, based on par…

- challenge page views
- challenge opt-ins
- eligible/submitted projects
- awarded projects
- workshop attendance
- resource link engagement
- mentor/office-hours usage for sponsor challenge
- project technologies used, based on participant-declared data

### PD-S095-B02 — Sponsor ROI and challenge adoption report — participant feedback about sponsor tools → recruiting/product-adoption metrics onl…

- participant feedback about sponsor tools
- sponsor feedback survey
- public result/project links
- configurable report branding/export
- recruiting/product-adoption metrics only with participant consent and clear data provenance

