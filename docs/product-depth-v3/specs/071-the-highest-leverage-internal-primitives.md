# PD-F071 — The highest-leverage internal primitives

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §71  
**Queue batches:** PD-F071-B01, PD-F071-B02, PD-F071-B03, PD-F071-B04, PD-F071-B05, PD-F071-B06

## Completion interpretation

This specification is the canonical depth contract for §71. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Section 71 defines architecture multipliers. Treat these as long-lived contracts with blast-radius risk, not low-risk convenience tasks.
- The registered type contract and rich-content applicability must be defined coherently even when research bullets were originally split across slices.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SAVED_VIEWS`
- `SCHEMA_EDITOR`
- `TYPE_REGISTRY`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | required |
| `search` | required |
| `docs` | required |

## Approved-design references

- No dedicated visual reference is required by default. Any UI introduced still follows the global Conflux v3 design system.

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

The feature atlas is intentionally much larger than any single release. The way to make it economically tractable is to build a small number of multipliers first.

### A. Frontend architecture multiplier

The current React application should gain:

- a real router with stable nested route semantics;
- a server-state/cache layer rather than bespoke `fetch` state in each screen;
- a generated typed client as the default request path;
- URL-addressable filters, selected objects and workspaces where appropriate;
- a component library for dense operator controls, not only cards/buttons;
- a standard async-operation surface;
- a standard data-grid/view surface;
- a standard inspector/drawer surface;
- a command framework and keyboard shortcut registry;
- a unified toast/notification/error model;
- a rich-document renderer/editor boundary;
- realtime subscription infrastructure where realtime is materially useful.

This is not framework churn for its own sake. It makes the large UI reconstruction feasible without multiplying bespoke state-management behavior.

### B. Operation plan / async job primitive

Many advanced features reduce to the same lifecycle:

1. select target set;
2. validate;
3. compute proposed changes;
4. show blast radius and warnings;
5. obtain approval if required;
6. execute atomically or as a durable job;
7. record per-object outcomes;
8. emit audit/webhooks;
9. allow retry of failed subset;
10. generate a receipt.

Assignment changes, bulk admissions, Event-as-Code apply, award finalization, publication, migration, large exports, extension installs and agent-proposed actions can all reuse this.

### C. Universal query/view primitive

One typed query AST should power:

- organizer filters;
- saved views;
- communications audiences;
- exports;
- bulk operations;
- analytics slices;
- CLI queries;
- MCP references;
- public search subsets where permitted.

This avoids six almost-but-not-quite-compatible filtering systems.

### D. Schema/extension primitive

A registered domain/config type should be able to declare:

- schema;
- human title/help;
- default;
- validation;
- secret fields;
- permissions;
- version;
- migration;
- audit behavior;
- Event-as-Code representation;
- generic UI rendering hints;
- API schema;
- extension ownership.

That is the path from VS42/VS43 into a genuinely extensible platform.

### E. Rich content primitive

One structured content model can support:

- project stories;
- public page rich text;
- sponsor challenge docs;
- event rules;
- announcements;
- feedback summaries;
- custom form help;
- documentation-like resources.

Each context can enable a subset, but security/rendering/accessibility logic should not be independently reinvented.

## Batch scope

### PD-F071-B01 — Internal primitives — frontend application architecture and reusable operator surfaces

- a real router with stable nested route semantics
- a server-state/cache layer rather than bespoke `fetch` state in each screen
- a generated typed client as the default request path
- URL-addressable filters, selected objects and workspaces where appropriate
- a component library for dense operator controls, not only cards/buttons
- a standard async-operation surface
- a standard data-grid/view surface
- a standard inspector/drawer surface

### PD-F071-B02 — Internal primitives — commands, errors, rich-content boundary and query consumers

- a command framework and keyboard shortcut registry
- a unified toast/notification/error model
- a rich-document renderer/editor boundary
- realtime subscription infrastructure where realtime is materially useful
- organizer filters
- saved views
- communications audiences
- exports

### PD-F071-B03 — Internal primitives — query consumers and registered-type contract foundation

- bulk operations
- analytics slices
- CLI queries
- MCP references
- public search subsets where permitted
- Define registered configuration type schema contract
- Define registered type human metadata contract
- Define registered type default and inheritance semantics

### PD-F071-B04 — Internal primitives — registered-type validation, versioning, migration, audit and rendering

- Implement registered type validation and normalization
- Implement secret-field representation and redaction
- Implement permission semantics for registered types
- Implement registered type schema versioning
- Implement registered type migrations
- Implement audit and semantic diff for registered configuration
- Implement Event-as-Code representation for registered types
- Implement generic UI rendering hints contract

### PD-F071-B05 — Internal primitives — registered-type API/ownership and rich-content adoption

- Expose registered type API/OpenAPI schema
- Define extension ownership and compatibility semantics
- project stories
- public page rich text
- sponsor challenge docs
- event rules
- announcements
- feedback summaries

### PD-F071-B06 — Internal primitives — rich-content adoption for forms and documentation

- custom form help
- documentation-like resources

