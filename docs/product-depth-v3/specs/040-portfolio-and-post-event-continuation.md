# PD-S040 — Portfolio and post-event continuation

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §40  
**Queue batches:** PD-S040-B01, PD-S040-B02

## Completion interpretation

This specification is the canonical depth contract for §40. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `DATA_GRID`
- `RICH_DOC`
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
| `archive` | required |
| `analytics` | required |
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

Post-event continuation can turn Conflux into durable project infrastructure without becoming a social network.
- BASE — participant portfolio of published projects.
- BASE — awards and event participation.
- BASE — opt-in public visibility.
- BASE — project page persists after event.
- ADV — post-event project updates clearly separated from judged snapshot.
- ADV — changelog/milestones.
- ADV — updated demo/repo links.
- ADV — continuation collaborators.
- ADV — organizer can archive/hide abusive or broken continuations.
- ADV — export portfolio data.
- ADV — static portfolio card/embed.
- EXPERT — project lineage across multiple events/iterations.
- EXPERT — attach publications/releases after event.
- EXPERT — immutable “as judged” tab alongside living project.
- PROG — portable project archive enables migration away from Conflux.

## Batch scope

### PD-S040-B01 — Portfolio and post-event continuation — participant portfolio of published proj… → continuation collaborators

- participant portfolio of published projects
- awards and event participation
- opt-in public visibility
- project page persists after event
- post-event project updates clearly separated from judged snapshot
- changelog/milestones
- updated demo/repo links
- continuation collaborators

### PD-S040-B02 — Portfolio and post-event continuation — organizer can archive/hide abusive or b… → portable project archive enables migrat…

- organizer can archive/hide abusive or broken continuations
- export portfolio data
- static portfolio card/embed
- project lineage across multiple events/iterations
- attach publications/releases after event
- immutable “as judged” tab alongside living project
- portable project archive enables migration away from Conflux

