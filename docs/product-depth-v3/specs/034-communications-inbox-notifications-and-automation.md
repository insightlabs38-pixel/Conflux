# PD-S034 — Communications, inbox, notifications and automation

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §34  
**Queue batches:** PD-S034-B01, PD-S034-B02, PD-S034-B03

## Completion interpretation

This specification is the canonical depth contract for §34. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `NOTIFICATIONS`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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
| `event_as_code` | required |
| `audit` | required |
| `webhook` | required |
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

Communications should be event-aware and audience-aware, not a generic mail blast form.
- BASE — announcements.
- BASE — targeted email/in-app delivery.
- BASE — participant inbox.
- BASE — scheduled send.
- BASE — delivery status.
- ADV — dynamic audience from saved query/view.
- ADV — preview exact recipient count before send.
- ADV — sample recipient preview.
- ADV — templates with structured variables.
- ADV — localization variants.
- ADV — quiet hours/timezone-aware delivery.
- ADV — digest mode.
- ADV — organizer approval before mass send.
- ADV — retry/bounce status from email provider.
- ADV — Discord/Slack webhook/channel delivery adapters.
- ADV — event-triggered automation: acceptance, deadline, check-in, result publication.
- ADV — unsubscribe/preference categories where legally appropriate.
- EXPERT — message sequence/campaign with stop conditions.
- EXPERT — communications audit including rendered template version.
- PROG — audience query + message template + schedule are configuration objects.

## Batch scope

### PD-S034-B01 — Communications, inbox, notifications and automation — announcements → sample recipient preview

- announcements
- targeted email/in-app delivery
- participant inbox
- scheduled send
- delivery status
- dynamic audience from saved query/view
- preview exact recipient count before send
- sample recipient preview

### PD-S034-B02 — Communications, inbox, notifications and automation — templates with structured variables → event-triggered automation: acceptance,…

- templates with structured variables
- localization variants
- quiet hours/timezone-aware delivery
- digest mode
- organizer approval before mass send
- retry/bounce status from email provider
- Discord/Slack webhook/channel delivery adapters
- event-triggered automation: acceptance, deadline, check-in, result publication

### PD-S034-B03 — Communications, inbox, notifications and automation — unsubscribe/preference categories where… → audience query + message template + sch…

- unsubscribe/preference categories where legally appropriate
- message sequence/campaign with stop conditions
- communications audit including rendered template version
- audience query + message template + schedule are configuration objects

