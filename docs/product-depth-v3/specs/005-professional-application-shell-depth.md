# PD-F005 — Professional application-shell depth

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §5  
**Queue batches:** PD-F005-B01, PD-F005-B02, PD-F005-B03

## Completion interpretation

This specification is the canonical depth contract for §5. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Use real route semantics rather than query-param pseudo-routing as the long-term navigation model; preserve drafts through deliberate state ownership rather than keeping every screen permanently mounted.
- Shell behavior must work with keyboard, narrow mobile, multiple roles, deep links and dense operator workflows.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `COMMANDS`
- `DATA_GRID`
- `NOTIFICATIONS`
- `PREVIEW_CONTEXT`
- `QUERY`
- `REALTIME`
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
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/app-shell`
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

- BASE: real route hierarchy with stable URLs, back/forward behavior and deep linking.
- BASE: event/workspace switcher with recent/favorite events.
- BASE: responsive persistent navigation that collapses to task-focused mobile navigation.
- BASE: breadcrumbs only where they add orientation.
- BASE: global command palette.
- BASE: global entity search.
- BASE: notification/inbox center.
- BASE: account/profile/preferences control.
- BASE: event state indicator (draft/open/judging/published/archived) always available but unobtrusive.
- ADV: recent objects and recent organizer actions.
- ADV: pinned organizer views.
- ADV: role switcher for users with multiple roles, with a clear “you are viewing as…” state.
- ADV: “preview as participant/judge/public” without unsafe impersonation.
- ADV: contextual side inspector that preserves list position.
- ADV: keyboard shortcut help overlay.
- ADV: configurable density: comfortable / compact / high-density.
- ADV: per-user table column preferences.
- ADV: workspace-aware tabs that preserve unsaved drafts.
- EXPERT: multi-pane operations mode for large desktop displays.
- EXPERT: command palette commands parameterized by selected entities.
- EXPERT: live operations mode with connection/realtime health state.
- PROG: route/view state is serializable enough to link to an exact operational context.

## Batch scope

### PD-F005-B01 — Professional application-shell depth — real route hierarchy with stable URLs,… → account/profile/preferences control

- real route hierarchy with stable URLs, back/forward behavior and deep linking
- event/workspace switcher with recent/favorite events
- responsive persistent navigation that collapses to task-focused mobile navigation
- breadcrumbs only where they add orientation
- global command palette
- global entity search
- notification/inbox center
- account/profile/preferences control

### PD-F005-B02 — Professional application-shell depth — event state indicator (draft/open/judgi… → configurable density: comfortable / com…

- event state indicator (draft/open/judging/published/archived) always available but unobtrusive
- recent objects and recent organizer actions
- pinned organizer views
- role switcher for users with multiple roles, with a clear “you are viewing as…” state
- preview as participant/judge/public” without unsafe impersonation
- contextual side inspector that preserves list position
- keyboard shortcut help overlay
- configurable density: comfortable / compact / high-density

### PD-F005-B03 — Professional application-shell depth — per-user table column preferences → route/view state is serializable enough…

- per-user table column preferences
- workspace-aware tabs that preserve unsaved drafts
- multi-pane operations mode for large desktop displays
- command palette commands parameterized by selected entities
- live operations mode with connection/realtime health state
- route/view state is serializable enough to link to an exact operational context

