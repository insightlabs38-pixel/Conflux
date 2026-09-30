# Conflux v3 design system — r2.1

Authoritative visual/interaction contract for all UI work. Legacy styling in `src/web/styles/*` is **not** a target.

## Files
| File | Purpose |
|---|---|
| `tokens.css` / `tokens.json` | Production tokens (light + dark). Replace `src/web/styles/tokens.css` values with these names/values (see `component-mapping.md`). |
| `v3.css` | Reference component grammar used by every prototype (buttons, forms, tables, shell, status, public/reading styles, icon mask set). Read it as a spec; do not ship it verbatim. |
| `prototypes/` | Standalone HTML of the D1 boards (Foundations, Component grammar, Directions, **Dark**) + screenshots. |
| `component-mapping.md` | Existing components → v3 targets, migrate/replace/new. |
| `../decisions/` | Written decisions (ADR-style). |

## Summary of the language ("Ledger")
- **Type**: IBM Plex Sans (UI), IBM Plex Mono (ids/code), Source Serif 4 (public long-form only). Scale 11/12/13/14/16/20/24/32 only. App page title max 20px.
- **Color**: cool neutral structure; ONE accent `#1d55c2` for action/selection/focus/links; semantic ok/warn/err/info/mute each with ink/tint/line. Every text pair ≥4.5:1 (measured, see Foundations board). Dark theme defined; public themes may override `--pub-accent` only after a contrast check.
- **Geometry**: radii 3/5/8; 4px spacing base; hairline borders carry hierarchy; shadow only on popover/dialog.
- **Density**: comfortable 44 / standard 36 (default) / dense 28 row heights; per-user; Dense is suggested once on ≈1800px+ operator displays and never auto-applied on resize (D-009); mobile targets ≥44px.
- **Status**: icon + word (+ tint only for summaries). Never colour alone. ≤1 tag per row.
- **Actions**: one primary per context; frequent actions visible; destructive neutral until final confirm button.
- **Shell**: 44px top bar, 216px rail (52px collapsed), right inspector 372–420px that preserves list position; participant/judge = top bar only; mobile = ≤5-item bottom nav + "More" sheet.
- **Grid**: role=grid, roving focus, J/K/arrows, X/Space select, Shift range, Enter inspect, E edit; virtualized; saved views; nested AND/OR filters with equivalent text query; bulk actions run on a frozen snapshot via plan → apply.
- **Public**: hero none/**compact (default 160–240px)**/standard/immersive (opt-in); project content near the fold; permanent project pages with living vs "as judged" versions.
- **Motion**: 120–180ms state transitions only; respects `prefers-reduced-motion`.
- **Anti-slop gate**: see Component grammar board (15 rules). Treat as a review checklist.

## Fonts
Loaded from Google Fonts in prototypes. Production must self-host (self-hostable product): Plex Sans 400/500/600, Plex Mono 400/500, Source Serif 4 400/600/400i, with system fallbacks already in `--font-*`.

## Icons
Lucide-compatible 24px stroke set rendered via CSS mask (`currentColor`). Prototype uses inline mask data-URIs only for portability; production should use the project's icon component.

## r2 additions
- **Dark mode** (`prototypes/html/Sys-Dark.html`, `../references/dark-mode/`): per-user *system / light / dark* for authenticated app surfaces; public pages stay organizer-themed. Theme root re-declares `color`/`background`; dark elevation = lighter raised layer + edge (D-008).
- **Responsive & wide** (`../references/responsive-wide/`): concrete 768 / 1024 / 1440 / ≥1800 rules and the wide-display density recommendation (D-009). Component grammar "Responsive rules" table updated.
- **Pairwise judging** reference added to `../references/judge-review/` (D-010).
- v3.css fixes: `.top` keeps 44px outside the shell grid; dark overrides for code blocks, step/count badges, scrim, popover surfaces.

### Known limitations (r2)
- (r2) `.btn` border was line-2 (≈1.7:1) — superseded in r2.1 (line-3). Fonts still load from Google Fonts in prototypes (they render with system fallbacks if blocked); production self-hosting and OFL notices belong to implementation.

## r2.1 changes
- **Outlined buttons use `line-3`** (light #8a929e 3.1:1, dark #7a8594 4.62:1) — D-008. Primary stays filled; ghost/text actions stay borderless; disabled = `surface-2` fill + `line` border + visible reason; panel/table hairlines unchanged (`line`/`line-2`). Checked on the densest toolbars (Data-Surface, Wide-1920, Story editor top bar, Builder-Plan): not noisy, so no compact/toolbar variant was introduced.
- v3.css: `.fig-chart` (theme-aware inline chart/diagram frame for fixtures) and `.fig-fail` (failed-media placeholder); `.tbl td.rowact` fits its 28px action and hides children rather than the cell.
- Board labels: Sys-Foundations `r2.1 · content inherited from r1` (plus spacing-label wrap and a missing ⓘ glyph fixed); Sys-Components `r2.1` (button grammar text states the border rule and control kinds); Sys-Dark `r2.1`; Sys-Directions `r2.1 · exploration record from r1`.
