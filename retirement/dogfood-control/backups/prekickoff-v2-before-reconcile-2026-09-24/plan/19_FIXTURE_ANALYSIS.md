# Official Fixture Analysis

## Shape
- event: `evt_01` / Sample Hack 2026
- submissions close: `2026-03-01T18:00:00Z` (therefore closed during the hackathon/judging period)
- tracks: 8
- judges: 30
- teams: 40
- projects: 41
- score records: 126
- per-project reviews: min 2, max 5, mean 3.07
- judge-project graph connected: True

## Deliberate duplicate
`prj_41` repeats `tm_07` / `Dry Harbour` / the same repository metadata as the earlier project while remaining a distinct fixture record. Import exactly; flag separately through duplicate detection.

## Constant scorer
`jdg_07` is the deliberate constant scorer (4/4/4 on all of that judge's recorded reviews). This invalidates casual per-judge z-score implementations and is a first-class normalization edge case.

## Test mutations to generate
Freebuff should derive cases with 0/1/many reviews, constant/extreme/sparse judges, disconnected/weakly connected assignment graphs, duplicate IDs/records, missing criteria, invalid timestamps, large event scale, and reordered import objects. Generated cases are disposable unless they expose a bug; minimize real failures into regressions.
