# App shell — design/app-shell (r2.1)
**Boards**: Shell-Organizer, Shell-Dense (⌘K), Shell-Overlays, Shell-Participant, Shell-Judge, Shell-Mobile
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Top bar + rail + right inspector for operators; top-bar-only for participant/judge; ≤5-item bottom nav + More sheet on mobile.
- Event switcher (current/favorites/recent), ⌘K palette with selection-parameterized commands, notification center with actionable rows, account menu with role switch + read-only preview-as + density + shortcuts.
- Overview is a *queue strip + needs-attention table*, not KPI cards; every figure links to filtered records.
- Live ops mode shows connection health and data age.

## Adaptable implementation details
- Exact rail width/labels (follow `roleDestinations`), icon choice, which widgets appear on Overview (saved-view driven).
- Palette ranking algorithm, notification grouping.

## Keyboard / focus / a11y
- Skip link first; rail is `nav` with aria-current; palette is dialog with listbox; `?` opens shortcuts; G-then-letter navigation.

## Known limitations
- Static comps; no real routing. Collapse/expand animation not shown.

## r2 changes
- **Shell-Participant** now 1280×860: the ready/frozen participant state (frozen banner, still-open items, team & project, day timeline, pass, where, help) instead of a shell-only stub. **Shell-Judge** now 1280×800 with a realistic 24-project workload (9-stop route table, pace bar with expected marker, drafts, recusal, flag awaiting organizer).
- Must preserve (added): the normal participant/judge screen is a full working page, never a blank canvas under the bar; judge overview summary strip stays ≤5 figures.
- Responsive: rail collapse / drawer / inspector-dock rules are now specified in `../responsive-wide/README.md` and D-009.
- Dark: `../dark-mode/` (Dark-Organizer, Dark-Overlays). Theme is a per-user preference on app surfaces only.
- Known limitations: Shell-Participant/Judge are single-state comps; the judge queue tab and route tab are separate references.

## r2.1 changes
- Shell-Mobile: organizer phone lists all 7 “Needs attention” items (r2 listed 4 under a count of 7); participant phone lists the full remaining day (13:00 → 20:30) instead of leaving an empty lower half.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
