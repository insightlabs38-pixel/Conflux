# PD-S083 — Code of Conduct acknowledgement and incident workflow

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §83  
**Queue batches:** PD-S083-B01, PD-S083-B02

## Completion interpretation

This specification is the canonical depth contract for §83. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Safety/Code-of-Conduct incidents use stricter authorization, audit and retention boundaries than ordinary moderation.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
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
| `analytics` | not_required |
| `search` | not_required |
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
- Do not turn incident tooling into broad surveillance or expose case data to ordinary organizers.

## Product requirements from research

Conflux has moderation/governance, but event-safety incidents are a distinct operational domain.

- BASE — published Code of Conduct.
- BASE — required acknowledgement at registration/check-in when configured.
- BASE — private incident-report form.
- BASE — named or anonymous reporting depending on event policy.
- BASE — restricted incident visibility to authorized safety staff.
- BASE — status: received / investigating / resolved.
- ADV — severity/category.
- ADV — incident assignment.
- ADV — evidence attachments.
- ADV — protective action notes.
- ADV — attendee restriction/ban integrated with check-in.
- ADV — internal immutable history.
- ADV — emergency contacts/resources.
- ADV — separate public communication from private case record.
- EXPERT — cross-event restriction lists only where the organization has an appropriate policy/legal basis.
- SECURITY — this domain should have stricter access/audit/retention than ordinary moderation.

**Why include:** MLH explicitly requires a clear incident-reporting system and Code of Conduct acknowledgement.

## Batch scope

### PD-S083-B01 — Code of Conduct acknowledgement and incident workflow — published Code of Conduct → incident assignment

- published Code of Conduct
- required acknowledgement at registration/check-in when configured
- private incident-report form
- named or anonymous reporting depending on event policy
- restricted incident visibility to authorized safety staff
- status: received / investigating / resolved
- severity/category
- incident assignment

### PD-S083-B02 — Code of Conduct acknowledgement and incident workflow — evidence attachments → this domain should have stricter access…

- evidence attachments
- protective action notes
- attendee restriction/ban integrated with check-in
- internal immutable history
- emergency contacts/resources
- separate public communication from private case record
- cross-event restriction lists only where the organization has an appropriate policy/legal basis
- this domain should have stricter access/audit/retention than ordinary moderation

