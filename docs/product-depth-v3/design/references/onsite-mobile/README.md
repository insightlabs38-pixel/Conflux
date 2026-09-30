# Onsite mobile — design/onsite-mobile (r2.1 · content unchanged from r1)
**Boards**: Onsite-A (scan, desk, pass), Onsite-B (route, mentor queue, pitch queue)
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Task-first layouts with one dominant ≥56px action; camera viewfinder with result card + exceptions; desk search with walk-ups; full-screen offline pass; judge route stops; mentor claim; stage timer/queue.

## Adaptable implementation details
- Camera library, haptics/sound, brightness API.

## Keyboard / focus / a11y
- Non-camera fallback (manual code) must exist; results announced via live region; large targets.

## Known limitations
- Camera view is a placeholder.

## r2.1 changes
- All outlined buttons now use the `line-3` border (D-008); no layout change.
