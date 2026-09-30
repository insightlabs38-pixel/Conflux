# Public project — design/public-project (r2.1)
**Boards**: Public-Project, Public-Project-Mobile
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Reading column ≤68ch serif; metadata card panel; version switch (Living vs As judged) with banner; numbered math, code with filename/copy, figures with captions/alt/long description, benchmark table; references; on-this-page nav; responsive media and in-box scroll for wide math/code.

## Adaptable implementation details
- Sidebar contents per project metadata; OpenGraph card.

## Keyboard / focus / a11y
- Figures have alt text + long description link; code/math scroll inside container; sticky TOC does not trap focus.

## Known limitations
- Long-description and MathML output not drawn.

## r2.1 changes
- Public-Project: Figure 1 is a compact real architecture diagram (Ingest → Embed → Sequence model → Calibrate); Figure 2 is the real “Forecast MAE by horizon” chart. Artboard 2110 → 2010 (placeholder height removed).
- Public-Project-Mobile: vertical architecture diagram; adds Figure 2 and Limitations from the desktop page; artboard 1500 → 1600 (full page height). The as-judged phone stays short on purpose (frozen snapshot).
- All outlined buttons now use the `line-3` border (D-008); no layout change.
