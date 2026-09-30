# PD-S031 — Community voting and abuse resistance

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §31  
**Queue batches:** PD-S031-B01, PD-S031-B02, PD-S031-B03

## Completion interpretation

This specification is the canonical depth contract for §31. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/organizer-data-surface`
- `design/public-event`
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

Community voting should remain optional but can become substantially more robust.
- BASE — clearly separate community vote from judge score.
- BASE — event-defined voting window.
- BASE — one-person/project constraints as configured.
- BASE — moderated project visibility.
- ADV — ranked voting / limited vote budget / favorites.
- ADV — category-specific voting.
- ADV — vote receipt visible to voter.
- ADV — anti-automation throttles.
- ADV — suspicious-pattern queue.
- ADV — transparent invalidation reason.
- ADV — re-run results after invalidated votes with audit.
- ADV — geographic/IP/device signals treated only as risk signals, not identity truth.
- ADV — organizer-set eligibility to vote: registered, accepted, checked-in, public.
- EXPERT — anomaly analytics with explainable features.
- EXPERT — privacy-preserving aggregate risk metrics.
- EXPERT — deterministic fraud-review case bundles.
- PROG — voting method/version embedded in result publication evidence.

## Batch scope

### PD-S031-B01 — Community voting and abuse resistance — clearly separate community vote from ju… → anti-automation throttles

- clearly separate community vote from judge score
- event-defined voting window
- one-person/project constraints as configured
- moderated project visibility
- ranked voting / limited vote budget / favorites
- category-specific voting
- vote receipt visible to voter
- anti-automation throttles

### PD-S031-B02 — Community voting and abuse resistance — suspicious-pattern queue → deterministic fraud-review case bundles

- suspicious-pattern queue
- transparent invalidation reason
- re-run results after invalidated votes with audit
- geographic/IP/device signals treated only as risk signals, not identity truth
- organizer-set eligibility to vote: registered, accepted, checked-in, public
- anomaly analytics with explainable features
- privacy-preserving aggregate risk metrics
- deterministic fraud-review case bundles

### PD-S031-B03 — Community voting and abuse resistance — voting method/version embedded in result publication evidence

- voting method/version embedded in result publication evidence

