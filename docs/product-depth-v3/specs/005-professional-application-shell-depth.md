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


## PD-F005-B01 canonical contract

Written by PD-F005-B01-T00 against the approved design (`design/app-shell`, `design/state-matrix`; boards Shell-Organizer, Shell-Dense, Shell-Overlays, Shell-Participant, Shell-Judge, Shell-Mobile; responsive rules in `design/references/responsive-wide/README.md` and D-009). Evidence: `docs/verification/PD-F005-B01/T00-census.log`. Escalation: ESC-20260930-007 (resolved, option A).

### What exists (reuse, do not rebuild)

- **Route model.** `src/web/lib/routes.ts` (hierarchy `/`, `/w/:workspace/:view`, `/person`, `/event`, `/api-explorer`; base path; `legacyTarget` for the pre-router query-string URLs) and `src/web/lib/urlState.ts` (location pushes, context params `event`/`stage`/`plan` carried between views, panel state replaced and dropped on view exit, the single-use `invite` token, nothing typed ever in a URL). 39 call sites. `WorkspaceRoute` already sends a view the role does not have to the overview.
- **Navigation.** `roleDestinations` (`WorkspaceNavigation.tsx`) is the one list of places per role; `WorkspaceNavigationProvider` hides optional modules that are off. `AppShell` has the skip link, rail with `aria-current`, a drawer on narrow screens and an account `details` menu (profile link, role, sign out).
- **Inbox and preferences.** `GET /workspaces/{w}/inbox/` and `POST .../inbox/{id}/read/` (member-scoped, `communications/views.py`), the notification categories and per-channel preferences (`NOTIFICATIONS` primitive, `core/notifications.py`, `lib/notifications.ts`, shown in the Profile destination).
- **Query.** The `QUERY` primitive with `GET .../events/{e}/entities/` (the caller's catalogue, organizer and admin only today: `projects`, `applications`) and `.../entities/{key}/`.
- **Other.** `PreviewBar` and `lib/previewContext.ts` (B02), the realtime hub (`RealtimeProvider`), `Icon`, `Modal`, `useUrlParam`.
- Missing: any command or shortcut registry, any palette or search UI, the inbox UI outside the Messages destination, any favorite or recent event, any theme control, and a breadcrumb.

### Canonical source of truth and names

- **Routes (primitive ROUTER, ESC-007 option A).** `routes.ts` and `urlState.ts` stay the only place a path or navigation query string is composed; T01 extends them in place: a typed `RouteTarget = { view, section?, event?, params? }` and one `routes.target(workspaceId, target)` builder, `section` as the existing top-level tab param, `event` staying a context search param (a workspace's views are shared across events, and old invite and bookmark URLs carry it). Search results, palette entries, breadcrumbs, the switcher and the inbox all produce a `RouteTarget`, never a string. PD-F071-B01-T01 later formalises these modules.
- **Destinations.** `roleDestinations` and the provider's hidden-module filter remain the only list of places. Rail, mobile bar, palette "go to" entries, search destination hits and breadcrumbs all derive from it; no component keeps its own list.
- **Commands (primitive COMMANDS, ESC-007 option A).** One registry, `src/web/lib/commands.ts`, created by T05: `Command { id, label, keywords, group, when(context), run(context), shortcut? }` with `context = { role, workspaceId, eventId, navigate }` (selection joins it in B03-T04). The palette is its reference consumer; the shortcut overlay (B02-T07) and selection-parameterised commands (B03-T04) read the same registry. Ranking is deterministic (prefix, then word, then subsequence, then recency), no model.
- **Shell preferences.** One module, `src/web/lib/shellPreferences.ts`, owns everything the shell remembers: theme (`system`, `light`, `dark`), favorite events, recent events. Keys are `conflux:v1:<user public id>:<workspace id>:<name>`; values are typed and validated on read; a stored event id is only used after it matches the events the server returned; recents are capped at 8, favorites at 12. The store is cleared on sign-out. It is device-local by decision (below).

### Lifecycle, state and authority

- **No server state is added by this batch.** No table, endpoint, SDK operation or migration. The server stays authority for what a person can see (routes, entities, inbox); the shell only narrows the presentation. A URL or stored value is a request: an unknown or no-longer-visible event, view or record is treated as absent and the URL is corrected with `replace` (urlState rules).
- **Switcher (T02).** Workspaces come from `useMe().memberships`; events from the lists the role's workspace already loads. Current, favorites and recents are shown (design); choosing one is a context push (Back returns), clears dependent params (`stage`, `plan`) and records a recent. A favorite is an explicit toggle; a recent is recorded on selection, not on every navigation.
- **Navigation (T03).** At most five bottom destinations plus a More sheet on phones (the first four destinations of the role and More when there are more than five); rail with groups on desktop; participant and judge keep top-bar navigation per the boards. Every overlay (drawer, More sheet) closes on Escape and returns focus; touch targets are 44px.
- **Breadcrumbs (T04).** Shown only where they add orientation: a record or section two levels below a destination ("Participants › Team Alpha"), never on a destination itself (V-SLOP-7 forbids repeating the title). One `Breadcrumbs` component takes `RouteTarget`s and labels from the page, so no feature builds its own trail.
- **Palette (T05).** `⌘K`/`Ctrl+K` opens a dialog with a listbox; commands in B01 are navigation and safe reads only (go to a destination or section, switch event, open inbox, theme, sign out). A command never mutates domain state itself: a mutating command must call the canonical endpoint through the shared client and show the standard consequence step (none ships in B01). `when()` hides what the role or an off module does not have; the server still refuses.
- **Global entity search (T06).** Web-only fan-out over `QUERY`: for each entity in the caller's own catalogue, a `contains` filter on that entity's label field, 200 ms debounce, in-flight requests aborted, at most 5 hits per entity, results grouped under the entity's label and linked by `RouteTarget`; destination, section and event matches come from the client lists. `src/web/lib/searchTargets.ts` maps each entity key to `{ labelField, view, section, param }` and a contract test fails when a registered entity has neither a target nor a recorded exclusion, so a new entity forces a decision. Free text never enters the URL. Because the catalogue is organizer and admin only, participants and judges search destinations and events only (stated limitation, nothing widened).
- **Inbox (T07).** A header control with the unread count and a panel of the member's inbox rows (existing endpoint), marking one row read through the existing call, a link to the full Messages destination and to notification preferences; refreshed through the realtime hub hint and on open. Empty, loading, error (data preserved, retry) and permission states follow `design/state-matrix`.
- **Account (T08).** The existing account menu keeps its profile link, role and sign out and gains the notification preferences link and the theme choice. Theme applies `data-theme` to the app root only (public event pages keep the organizer's preset), defaults to the operating system setting, and uses the approved dark token set. The menu is built from sections so B02 adds role switch, preview as, density and shortcuts to it without a second menu.

### Migration and compatibility

- Every existing URL keeps working (`legacyTarget`, `/w/:id` redirect, unknown view to overview). New query params are additive and optional (`section` already exists). No persisted server value changes.
- Device-local keys are new and versioned (`v1`); nothing reads the one existing key (`JudgeWorkspace` drafts), which stays as is.
- Browser tests that find the rail toggle or the account menu by text keep working: the visible labels "Navigation", "Back to workspaces" and the account summary label are retained, or the finders change in the same task and are listed in the receipt.
- The release note goes in `docs/operations/UPGRADES.md` at T91.

### Surface matrix, as interpreted for this batch

| Surface | Requirement | Closed by |
|---|---|---|
| `web` | required | T01-T08, T90, T91 |
| `api`, `sdk`, `cli`, `mcp`, `event_as_code`, `webhook`, `archive`, `analytics` | not_required | no endpoint, operation, tool, event or index is added |
| `audit` | required | no new event type. Shown by T90/T91: every mutation reachable from the palette or inbox (mark read, sign out) goes through the existing audited endpoint, the Operations and audit destination is reachable from the palette for exactly the roles that can read it, and the shell writes no state of its own |
| `search` | required | T06 (global entity search over the existing entity catalogue) |
| `docs` | required | `docs/operations/VISUAL_FOUNDATION.md` shell section and `UPGRADES.md` at T91 |

### Reuse and forbidden duplicates

- Forbidden: a second route table or any hand-built path or navigation query string; a second list of destinations; a second command or shortcut registry; a second preference store (every remembered value goes through `shellPreferences`); a new endpoint or table for inbox, search or recents; a client-side permission decision (the shell hides, the server refuses); typed text, ids of other people or personal data in a URL or in storage; ids typed by a person (V-SLOP-12, use `RecordPicker`).
- `ASYNC_JOB` (the declared reuse) is the only source for any slow, cancellable shell work; B01 has none, and the palette and search show progress only for their own debounced reads.

### Decisions taken here (conservative defaults, reversible)

- ROUTER and COMMANDS: adopt forward (ESC-20260930-007). The F071 owner tasks must adopt `routes.ts`, `urlState.ts` and `commands.ts`.
- Shell preferences are device-local (QUESTIONS.md, 2026-10-07T21:40Z). Moving them to a per-user server store later changes only `shellPreferences.ts`; B02 density and B03 column preferences should decide whether to join it.
- Task order inside the batch: T01 (route targets) first because everything produces one; then T03 and T04 (navigation, breadcrumbs), T02 (switcher, which creates `shellPreferences`), T08 (account and theme, which adds the theme to it), T07 (inbox), T06 (search), T05 (palette last, since it lists what the others expose).

### Test strategy

- Vitest: `routes`/`urlState` round trips for `RouteTarget` and every legacy URL; `shellPreferences` validation, caps, revalidation and clearing on sign-out; command registry (`when`, ranking, hidden modules); search target contract (every registered entity covered); component tests per overlay for keyboard, Escape and focus return.
- Playwright (read-only tier, seed 7, then isolated fixtures for anything that writes): deep link reload and Back/Forward per role, switcher with favorites and recents, rail at 1440 and bottom bar with More at 390, palette open, filter, run and close by keyboard, search hits for an organizer and destination-only for a participant, inbox open with unread count and mark read, theme switch with axe on both themes; all at 1440 and 390, plus the `slop-audit` gate unchanged.
- Python: no new tests unless a server change appears (none planned); `test_feature_search` and the registry tests must stay green.

### Escalation conditions

- A needed shell behavior that cannot be done without a new endpoint, table or entity registration (each registered entity needs a feature, manifest and search claim); a command that would have to mutate state; a route change that breaks a legacy URL; a theme that fails the contrast gate; any stored value that would need to leave the device.
