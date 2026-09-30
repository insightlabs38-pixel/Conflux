# Public event — design/public-event (r2.1)
**Boards**: Public-Event (no artwork), Public-Event-Themed (organizer theme, standard hero), Public-Event-Mobile
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Compact hero default with typographic fallback; status + one primary action; results near top when published; project gallery (cards allowed here); tracks/schedule/sponsors/resources; theme limited to accent+bg with contrast validation.

## Adaptable implementation details
- Section order (block-driven), card content, sponsor tier layout.

## Keyboard / focus / a11y
- Landmarks (nav/main/footer), h1 once, colour contrast validated, focus visible on themed accents.

## Known limitations
- Immersive hero not drawn.

## r2.1 changes
- Public-Event-Themed artboard 1100 → 1000 (≈180px of artboard slack above the theme strip).
- Public-Event-Mobile: winners/schedule rows no longer inherit the 88px project-row minimum; schedule gains the 19:00 item and calendar link; the themed phone mirrors the desktop page (“Last year’s projects”, secondary action) plus a page footer on both phones; artboard 1500 → 1420.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
