# Implementation handoff — how a task uses the Conflux v3 design
Frozen by PD-DESIGN-B00-T07. Authority order for UI work: task fields, then the cited `design_refs` (below), then the contracts here. Prototype CSS is a spec to read, never to ship; legacy `src/web/styles/*` is not a target.

## What to cite
| Cite | Where | Holds |
|---|---|---|
| a `design/<id>` | `DESIGN_MANIFEST.yaml` `references` | status, artifacts (README, HTML, screenshots), viewport and state coverage, `must_preserve`, `adaptable_details` |
| `V-*` | `system/VISUAL_CONTRACT.md` | type, spacing, density, colour, theme, borders, elevation, radii, icons, motion, focus, hero, responsive, 15 anti-slop rules |
| `S-*` | `states/STATE_MATRIX.md` | eleven state classes and the per-surface coverage table |
| `D-nnn` | `decisions/` | D-001..D-012 (D-011 rail size and type floor, D-012 touch hit area and hero budget) |
| `F-n`, `O-n` | `reviews/B00_APPROVAL.md` | review findings and implementation obligations |

## Must preserve vs adaptable
Each reference README has both lists and the manifest repeats them as `must_preserve` and `adaptable_details`. Must preserve means hierarchy, dominant action, interaction order, state behaviour, density, accessibility semantics and every V-/S- rule. Adaptable means copy, icon choice, exact column sets, widget internals, section order where block-driven, and the algorithms (palette ranking, notification grouping). A deviation from a must-preserve item is a design decision in `decisions/`, not a quiet edit.

## Obligations the visual foundation (PD-F004 onward) inherits
- Tokens: replace `src/web/styles/tokens.css` values with `system/tokens.css` names and values, with a `--space-*` to `--sp-*` alias layer for one release (`component-mapping.md`); add `--h-touch`; self-host the fonts.
- Components: split Badge into Status (icon plus word) and Tag; at most one tag per row; forbid nested Card; extend the four state components with the S- fields (kept data, retry scope, error reference, next action, reason, cancel after 8 s); build avatar and count text at 11px; 44px hit areas on touch.
- DataGrid: roving focus with J/K/arrows, X/Space and Shift range, Enter inspect, E edit, V views, F filter; `aria-sort`, `aria-rowcount`; inspector keeps list position and returns focus (O: `components/DataGrid.tsx` has arrows, Home/End and paging only).
- Server authority: reveal of masked values is an audited server action (O-1); inspector mutations go through canonical services with version and idempotency conflicts shown (O-2); check-in eligibility is the server's verdict (O-3); rich and diagram content goes through `core/rich.py` (O-4); approval counts come from the `APPROVAL` policy (F-5).
- Rail: organizer follows `roleDestinations` (D-011); features not enabled are absent, not disabled.
- Sponsor and the "design first" list in `LATER_DESIGN_PASSES.md` need their own pass before their batch; they inherit Ledger until then.

## Rebuilding the artifacts
`python3 docs/product-depth-v3/design/exports/r2.1/tools/sync-canvas.py && node docs/product-depth-v3/design/exports/r2.1/tools/build-exports.mjs --shots`. The committed files are authoritative; nothing depends on the hosted canvas (`exports/r2.1/SOURCE.md`).
