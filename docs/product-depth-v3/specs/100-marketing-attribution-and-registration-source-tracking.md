# PD-S100 — Marketing attribution and registration-source tracking

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §100  
**Queue batches:** PD-S100-B01

## Completion interpretation

This specification is the canonical depth contract for §100. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- No cross-site tracking or browser fingerprinting.

## Product requirements from research

A modest feature, not an ad-tech stack.

- BASE — optional registration-source field.
- BASE — UTM/referral capture.
- ADV — campaign/source funnel: visit → register → confirm → check in → submit.
- ADV — partner/referral link.
- ADV — outreach channel comparison.
- ADV — recurring-event invite cohort.
- ADV — public event page conversion.
- EXPERT — privacy-preserving aggregate reporting.
- DO NOT BUILD — cross-site tracking/fingerprinting.
- DO NOT BUILD — marketing automation suite.

**Why include:** Organizers need to know whether outreach worked; recurring programs especially benefit.

## Batch scope

### PD-S100-B01 — Marketing attribution and registration-source tracking — optional registration-source field → privacy-preserving aggregate reporting

- optional registration-source field
- UTM/referral capture
- campaign/source funnel: visit → register → confirm → check in → submit
- partner/referral link
- outreach channel comparison
- recurring-event invite cohort
- public event page conversion
- privacy-preserving aggregate reporting

