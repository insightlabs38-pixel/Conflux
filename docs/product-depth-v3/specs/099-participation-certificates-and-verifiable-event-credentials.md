# PD-S099 — Participation certificates and verifiable event credentials

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §99  
**Queue batches:** PD-S099-B01, PD-S099-B02

## Completion interpretation

This specification is the canonical depth contract for §99. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Credentials use simple verification URLs/codes and revocation/correction. Do not add blockchain or redundant signature layers without a real portable-verification consumer.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
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
- No blockchain credentials or redundant cryptographic ceremony without a concrete external verifier.

## Product requirements from research

This is useful if kept simple.

- BASE — participation certificate for checked-in participants under configured eligibility.
- BASE — winner/finalist/judge/mentor/volunteer certificate templates.
- BASE — unique public verification URL or code.
- BASE — PDF generation.
- ADV — certificate eligibility from canonical attendance/submission/judging state.
- ADV — organizer revoke/correct/reissue.
- ADV — badge/credential metadata export.
- ADV — LinkedIn-friendly share link.
- EXPERT — Open Badges-compatible export if it remains low-complexity.
- DO NOT BUILD — blockchain credentials.
- DO NOT BUILD — layers of signatures over a simple verification URL unless a partner explicitly needs signed portable credentials.

**Why include:** Certificates are commonly requested, easy to derive from state Conflux already owns, and useful to participants/staff.

## Batch scope

### PD-S099-B01 — Participation certificates and verifiable event credentials — participation certificate for checked-i… → LinkedIn-friendly share link

- participation certificate for checked-in participants under configured eligibility
- winner/finalist/judge/mentor/volunteer certificate templates
- unique public verification URL or code
- PDF generation
- certificate eligibility from canonical attendance/submission/judging state
- organizer revoke/correct/reissue
- badge/credential metadata export
- LinkedIn-friendly share link

### PD-S099-B02 — Participation certificates and verifiable event credentials — Open Badges-compatible export if it remains low-complexity

- Open Badges-compatible export if it remains low-complexity

