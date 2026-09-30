# PD-S013 — Identity, profiles, privacy and user history

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §13  
**Queue batches:** PD-S013-B01, PD-S013-B02, PD-S013-B03

## Completion interpretation

This specification is the canonical depth contract for §13. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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

Profiles should become reusable infrastructure across registration, matching, judging expertise, mentorship and portfolios.
- BASE — name, avatar, bio, links and skills.
- BASE — granular visibility for public/event-only/private profile fields.
- BASE — one person can have multiple roles in different events.
- BASE — profile completeness feedback only when a workflow needs it.
- ADV — education/employment/organization history.
- ADV — skill taxonomy with proficiency/evidence.
- ADV — availability and timezone.
- ADV — social/repository links with verification status.
- ADV — reusable application answers with explicit consent before reuse.
- ADV — cross-event participation history.
- ADV — cross-event judge/mentor history.
- ADV — configurable pronouns/display-name fields without requiring them.
- ADV — account export and data-deletion workflow.
- ADV — delegated organization identity linkage.
- EXPERT — verified organization/domain membership.
- EXPERT — relationship/conflict declarations reused by judging.
- EXPERT — provenance for imported profile data.
- EXPERT — privacy-preserving matching features that need not expose all profile fields.
- PROG — schema for custom profile attributes with retention/visibility policy.

## Batch scope

### PD-S013-B01 — Identity, profiles, privacy and user history — name, avatar, bio, links and skills → social/repository links with verificati…

- name, avatar, bio, links and skills
- granular visibility for public/event-only/private profile fields
- one person can have multiple roles in different events
- profile completeness feedback only when a workflow needs it
- education/employment/organization history
- skill taxonomy with proficiency/evidence
- availability and timezone
- social/repository links with verification status

### PD-S013-B02 — Identity, profiles, privacy and user history — reusable application answers with expli… → relationship/conflict declarations reus…

- reusable application answers with explicit consent before reuse
- cross-event participation history
- cross-event judge/mentor history
- configurable pronouns/display-name fields without requiring them
- account export and data-deletion workflow
- delegated organization identity linkage
- verified organization/domain membership
- relationship/conflict declarations reused by judging

### PD-S013-B03 — Identity, profiles, privacy and user history — provenance for imported profile data → schema for custom profile attributes wi…

- provenance for imported profile data
- privacy-preserving matching features that need not expose all profile fields
- schema for custom profile attributes with retention/visibility policy

