# Conflux v3 visual-system contract — v1 (design revision r2.1)

Frozen by PD-DESIGN-B00-T02. This page is the rule list; values live in `tokens.css` / `tokens.json` (one source: the CSS is the json, enforced by `tests/test_design_manifest.py`). Rationale: `README.md`, `decisions/001-004, 008-009`. Legacy styling in `src/web/styles/*` is not an input. Changing a rule here, or a token value, is a design decision: add a `decisions/` entry and bump this version.

## Rules (ids are citable in reviews and tasks)
| Id | Area | Rule |
|---|---|---|
| V-TYPE-1 | Typography | IBM Plex Sans (UI), Plex Mono (ids, code, tokens), Source Serif 4 (public long-form only). Self-hosted in production, system fallbacks stay in `--font-*`. |
| V-TYPE-2 | Typography | Sizes come only from 11/12/13/14/16/20/24/32 (`--fs-*`); line heights `--lh-tight` 1.25, `--lh-ui` 1.4, `--lh-read` 1.65. App page titles are at most 20px; 24/32 are public pages only. |
| V-SPACE-1 | Spacing | 4px base, steps 4/8/12/16/20/24/32/40/48 (`--sp-*`). No other literal paddings or gaps. |
| V-DENS-1 | Density | Rows comfortable 44 / standard 36 / dense 28, controls 40/32/28. Standard is the default; Dense is an explicit per-user choice (offered once on about 1800px+ displays); density never changes with viewport. Touch targets stay at least 44px on mobile. |
| V-COLOR-1 | Color | Cool neutrals plus ONE accent (`--accent`) for action, selection, focus and links. Semantic ok/warn/err/info/mute each have ink, tint and line. |
| V-COLOR-2 | Color | Every text/surface pair is at least 4.5:1; control borders (`--line-3`) and focus at least 3:1, in light and dark. Status is icon plus word, never colour alone. Public themes may override `--pub-accent` only after a contrast check. |
| V-THEME-1 | Theme | Authenticated surfaces: system / light / dark per user (default system). A dark theme root re-declares `color` and `background-color`; public pages follow the organizer theme, not the app theme. |
| V-LINE-1 | Borders | Hierarchy comes from hairlines: `--line` panels and tables, `--line-2` inputs, `--line-3` outlined buttons. Ghost/text actions are borderless. |
| V-ELEV-1 | Elevation | Shadow only on floating layers (`--sh-pop` popover, `--sh-dlg` dialog). Dark raised layers are lighter plus an edge. No glass, blur or ambient motion. |
| V-RAD-1 | Radii | 3 / 5 / 8px (`--r-1..3`); `--r-pill` only for avatars and counts. |
| V-ICON-1 | Icons | Lucide-compatible stroke set, 16px in controls (24px grid), `currentColor`, no coloured tiles beside headings. |
| V-MOTION-1 | Motion | State transitions only, 120ms (`--t-fast`) to 180ms (`--t-base`); everything honours `prefers-reduced-motion`. |
| V-FOCUS-1 | Focus | Visible two-ring focus (`--focus`) on every interactive element; never removed. |
| V-HERO-1 | Compact hero | Public hero is none / compact (default, 160-240px) / standard (at most 360px) / immersive (opt-in, Advanced). Mobile at most 120px. Project content stays near the fold; missing art falls back to a typographic lockup. Operator screens have no hero. |
| V-RESP-1 | Responsive | Breakpoints wide 1440, desktop 1024, tablet 768, mobile below (`decisions/009`); mobile has at most five bottom-nav items plus More. |

## Anti-slop gate (review checklist; a violation needs a written exception)
V-SLOP-1 no gradients in chrome, buttons or backgrounds. V-SLOP-2 no coloured icon tiles. V-SLOP-3 no KPI-card grids (a summary strip of at most six figures linking to filtered records). V-SLOP-4 no nested cards. V-SLOP-5 no pill soup (at most one tag per row). V-SLOP-6 no oversized app titles or marketing copy in operator screens. V-SLOP-7 no repeated labels across breadcrumb, H1 and panel title. V-SLOP-8 no hidden primary actions in kebab menus. V-SLOP-9 no alarm pages (red only on the failing item and the final destructive button). V-SLOP-10 no fake AI affordances on deterministic flows. V-SLOP-11 no false precision (two decimals at most; dates in event timezone with a relative hint). V-SLOP-12 no opaque IDs as input. V-SLOP-13 no glass, blur or ambient motion. V-SLOP-14 no three-column card dashboards where a sortable table is the task. V-SLOP-15 screenshot test: any cropped region reads as mature production software.

## Verified, not asserted
`tests/test_design_manifest.py` recomputes WCAG contrast for every pair above in both themes, checks the type, spacing, radius, motion and density sets, and fails if `tokens.css` and `tokens.json` drift. Measured (light/dark): ink on surface 17.4/15.0, ink-3 5.7/6.7, accent 6.7/7.1, line-3 3.1/4.6. Hover, focus and axe behaviour are implementation QA (known limitation, README).

## Adopting it
Replacing `src/web/styles/tokens.css` values and the component grammar is PD-F004 onward (`component-mapping.md`), not this task; until then no web component reads these tokens.
