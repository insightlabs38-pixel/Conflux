# PD-S032 — Sponsor challenge and developer-resource center

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §32  
**Queue batches:** PD-S032-B01, PD-S032-B02, PD-S032-B03

## Completion interpretation

This specification is the canonical depth contract for §32. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `EXTENSION_MANIFEST`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `RICH_DOC`
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
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | required |
| `search` | required |
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

Sponsors can get a real subsystem instead of static logos plus prize text.
- BASE — sponsor profile and challenge description.
- BASE — prize/eligibility link.
- BASE — resources, docs, starter repositories and support contacts.
- BASE — FAQ.
- ADV — challenge-specific submission requirements.
- ADV — sponsor judge pool.
- ADV — workshop/session linkage.
- ADV — API key/credit claim instructions with access control.
- ADV — resource version/update notices.
- ADV — sponsor announcements scoped to challenge participants.
- ADV — challenge opt-in/bookmark.
- ADV — sponsor office hours.
- ADV — challenge analytics: views, opt-ins, eligible projects.
- ADV — sponsor portal with least-privilege permissions.
- ADV — sponsor feedback after judging.
- EXPERT — sandbox credential issuance via extension/integration providers.
- EXPERT — sponsor API usage evidence only where participants opt into collection.
- PROG — sponsor resource types are extension-friendly and archiveable.

## Batch scope

### PD-S032-B01 — Sponsor challenge and developer-resource center — sponsor profile and challenge descripti… → API key/credit claim instructions with…

- sponsor profile and challenge description
- prize/eligibility link
- resources, docs, starter repositories and support contacts
- FAQ
- challenge-specific submission requirements
- sponsor judge pool
- workshop/session linkage
- API key/credit claim instructions with access control

### PD-S032-B02 — Sponsor challenge and developer-resource center — resource version/update notices → sandbox credential issuance via extensi…

- resource version/update notices
- sponsor announcements scoped to challenge participants
- challenge opt-in/bookmark
- sponsor office hours
- challenge analytics: views, opt-ins, eligible projects
- sponsor portal with least-privilege permissions
- sponsor feedback after judging
- sandbox credential issuance via extension/integration providers

### PD-S032-B03 — Sponsor challenge and developer-resource center — sponsor API usage evidence only where p… → sponsor resource types are extension-fr…

- sponsor API usage evidence only where participants opt into collection
- sponsor resource types are extension-friendly and archiveable

