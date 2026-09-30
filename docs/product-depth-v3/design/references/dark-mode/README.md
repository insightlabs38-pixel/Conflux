# Dark mode — design/dark-mode (r2.1)
**Boards**: Dark-Organizer (shell + data surface), Dark-Judge (review), Dark-MyEvent (participant, action-needed + ready), Dark-Overlays (⌘K, scrim, focus, selection); foundations/components: `../../system/prototypes/html/Sys-Dark.html`
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

Representative, not exhaustive: the other surfaces inherit through tokens. Boards were produced by applying `[data-theme="dark"]` to the same markup as the light comps — no redrawing — which is what surfaced the token-scope fixes below.

## Must preserve
- Same geometry, type, density and single accent; only values re-map (`tokens.css` `[data-theme="dark"]`).
- Elevation in dark = lighter layer + 1px light edge + stronger shadow (`.pop/.dlg/.cmdk` use surface-2); scrim darker.
- Status still icon + word; semantic tints are deep low-chroma fills with lightened inks (text on own tint ≥7:1).
- **Theme scope re-declares `color` and background** (`[data-theme] { color: var(--ink); background: var(--bg) }`): body sets ink once from the light tokens, so a themed subtree otherwise inherits light-mode ink (found on the first dark comp).
- Primary-on-accent text uses `--accent-ink` (never hard-coded white); success/step/count badges on light dark-mode inks use dark text.
- QR codes and printable badges stay light (scanner quiet zone). Organizer media is not inverted.
- **Authority**: system / light / dark is a per-user preference for authenticated app surfaces (default System). Public event & project pages follow organizer theme tokens and are never overridden by the viewer's app theme; a "Dark base" public preset is an organizer choice contrast-checked at save. "Preview as public" in the builder renders the public theme.

## Measured contrast (dark)
ink/surface 14.98 · ink-2 9.03 · ink-3 6.69 (6.11 on surface-2) · accent/surface 7.08 · accent-ink/accent 7.69 · ok/warn/err ink on own tint 8.25/8.82/7.66 · mute 5.67 · accent/warn on surface-3 5.37/7.58 · control border line-3 4.62 (≥3). Lowest text pair 5.37:1. Semantic tint borders (~1.9:1) and hairlines are decoration.

## Adaptable implementation details
- System preference source (`prefers-color-scheme`) and persistence; exact shadow strengths.

## Known limitations
- Not comped: public pages, story editor, builder, deliberation, onsite. Outlined buttons use `line-3` (4.62:1 in dark) since r2.1 (D-008).

## r2.1 changes
- Dark-Judge: Figure 2 is a real inline chart “Forecast MAE by horizon” (token-driven, reads in dark).
- Dark-Organizer: shares the Data-Surface fixes (row-action ellipsis fragment removed, row hairlines reach the inspector, Changed column 96px).
- All outlined buttons now use the `line-3` border (D-008); no layout change.
