# PD-S086 — Dietary needs, meal planning and distribution

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §86  
**Queue batches:** PD-S086-B01, PD-S086-B02

## Completion interpretation

This specification is the canonical depth contract for §86. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Dietary/allergy data is restricted sensitive operational data with explicit retention; meal distribution is not a catering ERP.

## Canonical primitive reuse

- `ASYNC_JOB`
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
| `analytics` | required |
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

## Product requirements from research

Do not become catering software; solve the organizer counts and participant entitlement problem.

- BASE — dietary/allergy fields during registration.
- BASE — aggregate counts for authorized organizers.
- BASE — meal schedule.
- ADV — meal entitlement by checked-in status/role.
- ADV — QR/badge meal claim.
- ADV — count remaining/served.
- ADV — dietary label shown only to appropriate distribution staff, not publicly.
- ADV — meal vendor count export.
- ADV — shortage warning from RSVP/check-in counts.
- ADV — organizer can mark special meal pickup.
- ADV — unused/overage estimate for post-event analysis.
- SECURITY — allergy/dietary data gets restricted visibility and retention controls.

**Why include:** Food and dietary planning is explicitly ordinary hackathon work and currently falls outside most competition platforms.

## Batch scope

### PD-S086-B01 — Dietary needs, meal planning and distribution — dietary/allergy fields during registrat… → meal vendor count export

- dietary/allergy fields during registration
- aggregate counts for authorized organizers
- meal schedule
- meal entitlement by checked-in status/role
- QR/badge meal claim
- count remaining/served
- dietary label shown only to appropriate distribution staff, not publicly
- meal vendor count export

### PD-S086-B02 — Dietary needs, meal planning and distribution — shortage warning from RSVP/check-in cou… → allergy/dietary data gets restricted vi…

- shortage warning from RSVP/check-in counts
- organizer can mark special meal pickup
- unused/overage estimate for post-event analysis
- allergy/dietary data gets restricted visibility and retention controls

