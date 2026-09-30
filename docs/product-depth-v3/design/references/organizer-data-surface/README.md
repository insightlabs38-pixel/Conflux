# Organizer data surface — design/organizer-data-surface (r2.1)
**Boards**: Data-Surface, Data-Filters
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Grid + right inspector; saved-view control with modified/reset/save/copy link; chips + nested group affordance + equivalent query line; group rows with aggregates; selection bar with frozen-snapshot bulk plan; async job banner; inline cell edit with validation; dense 28px rows and virtualization footer; keyboard hint bar.

## Adaptable implementation details
- Column set per page; which actions sit in the bulk bar (max 4 + More); chip visual details; job banner placement (may live in Operations).

## Keyboard / focus / a11y
- role=grid, roving tabindex, aria-rowcount, sortable headers with aria-sort, selection announced ("3 selected"), inspector focus return.

## Known limitations
- Board view is only named (List/Board toggle), not designed. Column resize/reorder handles not drawn.

## r2 changes
- Data-Filters artboard trimmed to 1350×1000 (r1 had a dead strip on the right). Data-Surface unchanged.
- New companions: `../responsive-wide/` **Resp-1024** (docked inspector, two-line name cell, folded toolbar) and **Wide-1920** (5,012-person stress fixture, 10 columns, inspector stays 420px). Dark: `../dark-mode/Dark-Organizer`.
- Must preserve (added): extra width is spent on columns and readable values, never on stretched inspector/cards; at ≥1800 suggest Dense once (per-user); virtualization cues (row window, tiny thumb, server-side sort/query) are visible.
- Known limitations (r2): stray hairline fragment on the cursor row; Changed column tight at 1440 — both fixed in r2.1.

## r2.1 changes
- Data-Surface: the “stray hairline fragment” at the inspector edge was the cell’s `text-overflow: ellipsis` drawing “…” because the 28px row-action button overflowed the 44px column’s 24px content box. Fix: `.tbl td.rowact` padding 6px + `text-overflow: clip`.
- Data-Surface: unhovered rows’ hairlines stopped short of the inspector because `visibility:hidden` hid the whole action cell (border included). Fix: hide the cell’s children, not the cell.
- Changed column 80 → 96px (Name 182, Waiver 144, Table 58); Team keeps ~179px so “Northwind Grid Forecaster” is not truncated. Same density, same column set.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
