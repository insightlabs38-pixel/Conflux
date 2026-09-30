# Component mapping — existing code → v3

Inventory from `src/web/components` and `src/web/features` (functional behavior stays; visuals are replaced).

| Existing | v3 target | Action |
|---|---|---|
| `styles/tokens.css`, `main.css`, `components.css`, `presentation.css` | `design/system/tokens.css` + component classes per `v3.css` | **Replace** values; keep token *names* where they overlap (`--space-*`→`--sp-*` alias layer allowed for one release). |
| `components/AppShell.tsx`, `WorkspaceNavigation.tsx` (`roleDestinations`) | Top bar + rail + inspector slot (D2). Keep role→destination table and groups (Manage event / Advanced / Account). | **Restyle + restructure**; add event switcher, ⌘K, notifications, role switcher, density; real routes (spec 005). |
| `Button.tsx`, `Badge.tsx` | `.btn` (pri/sec/ghost/dng-o/icon, sm/md/lg); `.st` inline status + `.tag` | **Migrate**. Badge splits into `Status` (icon+text) and `Tag`. Remove colour-only variants. |
| `Card.tsx` | `.pn` (single level) / `.well` | **Reduce usage**; forbid nested Card. |
| `EmptyState`, `ErrorState`, `LoadingState`, `DeniedState` | State matrix D12 patterns | **Migrate**; add "data kept / retry scope / error ref" props. |
| `Person.tsx` | `.avatar` + name/role text | Migrate. |
| `WorkflowSections.tsx` | Accordion rows (`.acc`) / checklist (`Getting live`) | Migrate. |
| `features/teams/ParticipantOverview`, `TeamPanel` | D4 My Event hub (derived from canonical state) | **New composition**, reuse data hooks. |
| `features/submissions/SubmissionPanel`, `FrozenSubmissionPreview` | D5 story editor + D9 as-judged snapshot | Reuse frozen-preview logic; new editor. |
| `features/judging/JudgeWorkspace`, `JudgeDesk`, offline tests | D6 three-pane + narrow mode | Keep offline-buffer/reconcile behavior; new layout. |
| `features/awards/AwardsPanel`, `PublicAwards` | D7 decision room, D8 results | Keep proposals/approval logic. |
| `features/operations/OperationsCenter`, `OperatorConsole` | D2 Overview + D3 ops mode | Restructure to queue strip + saved-view widgets. |
| `features/event-builder/*`, `stage-builder`, `form-builder`, `policy-builder`, `page-builder` (`ConfigFields`, `configSchema`, `blockSchemas.generated`) | D10 setup / pages / plan-apply | Keep schema-driven fields; new progressive-disclosure layout, diagnostics rail, plan view. |
| `features/integrations`, `api-explorer` | Advanced group, extension config (D10 Plan) | Restyle. |
| (none) | **DataGrid + SavedViews + FilterBuilder + BulkPlanDialog + Inspector** | **New shared primitives** (`DATA_GRID`, `SAVED_VIEWS`, `QUERY`, `BULK_PLAN`). |
| (none) | CommandPalette, NotificationCenter, EventSwitcher, ShortcutHelp | New shell primitives. |
| (none) | Public `Hero` (none/compact/standard/immersive), `ProjectPage`, `VersionSwitch` | New public components (spec 004). |
