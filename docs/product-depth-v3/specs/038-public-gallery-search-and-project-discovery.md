# PD-S038 — Public gallery, search and project discovery

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §38  
**Queue batches:** PD-S038-B01, PD-S038-B02, PD-S038-B03

## Completion interpretation

This specification is the canonical depth contract for §38. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`

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

- `design/public-event`
- `design/public-project`
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

The gallery can become an excellent technical-project discovery surface rather than a card grid.
- BASE — fast search.
- BASE — track/tag filters.
- BASE — sort options with explicit semantics.
- BASE — strong project cards.
- BASE — accessible project detail pages.
- ADV — full-text search over project story and metadata.
- ADV — filter by technologies/custom taxonomy/award/status.
- ADV — saved/shareable public searches.
- ADV — featured collections curated by organizer.
- ADV — random/discovery mode that does not bias official ranking.
- ADV — related projects by explicit tags; ML similarity optional.
- ADV — compare projects.
- ADV — filter to projects with demo/repo/paper/dataset.
- ADV — static archive search after event.
- EXPERT — public search syntax for power users.
- EXPERT — federated search across events in a workspace/org.
- PROG — public search API respects publication/retention policy.

## Batch scope

### PD-S038-B01 — Public gallery, search and project discovery — fast search → saved/shareable public searches

- fast search
- track/tag filters
- sort options with explicit semantics
- strong project cards
- accessible project detail pages
- full-text search over project story and metadata
- filter by technologies/custom taxonomy/award/status
- saved/shareable public searches

### PD-S038-B02 — Public gallery, search and project discovery — featured collections curated by organiz… → federated search across events in a wor…

- featured collections curated by organizer
- random/discovery mode that does not bias official ranking
- related projects by explicit tags; ML similarity optional
- compare projects
- filter to projects with demo/repo/paper/dataset
- static archive search after event
- public search syntax for power users
- federated search across events in a workspace/org

### PD-S038-B03 — Public gallery, search and project discovery — public search API respects publication/retention policy

- public search API respects publication/retention policy

