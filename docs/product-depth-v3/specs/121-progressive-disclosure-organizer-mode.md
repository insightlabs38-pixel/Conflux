# PD-S121 — Progressive-disclosure organizer mode

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §121  
**Queue batches:** PD-S121-B01

## Completion interpretation

This specification is the canonical depth contract for §121. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Progressive disclosure is a persistent information-architecture rule: disabled systems disappear and expert features stay discoverable without cluttering base workflows.

## Canonical primitive reuse

- `ASYNC_JOB`
- `COMMANDS`
- `QUERY`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | not_required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | not_required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/event-builder`
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

Given Conflux's eventual feature depth:

- default navigation only shows enabled systems;
- setup wizard asks intent, then enables relevant modules;
- advanced controls remain under explicit “Advanced” disclosure;
- expert features can be pinned by frequent users;
- settings search jumps directly to hidden configuration;
- command palette exposes power operations without cluttering every page;
- documentation/help links are contextual.

**Outcome:** extreme capability without intimidating first-time organizers.

## Batch scope

### PD-S121-B01 — Progressive-disclosure organizer mode — Progressive disclosure: default navigat… → Progressive disclosure: documentation/h…

- Progressive disclosure: default navigation only shows enabled systems
- Progressive disclosure: setup wizard asks intent, then enables relevant modules
- Progressive disclosure: advanced controls remain under explicit “Advanced” disclosure
- Progressive disclosure: expert features can be pinned by frequent users
- Progressive disclosure: settings search jumps directly to hidden configuration
- Progressive disclosure: command palette exposes power operations without cluttering every page
- Progressive disclosure: documentation/help links are contextual

