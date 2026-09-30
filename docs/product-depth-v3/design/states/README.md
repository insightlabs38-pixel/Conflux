# State matrix (design/state-matrix, r2.1)
Boards: `html/States-1.html` (normal, loading, empty, partial, error, permission-denied) and `html/States-2.html` (validation, large/dense, destructive, mobile, offline/degraded). Screenshots in `screenshots/`.
Each state class has one rule; each UI task must implement the rule on its surface. Rules are listed in the left column of every row.
Known limits: representative surfaces only (grid, My Event, judge, deliberation, story, public project, builder, pass); other surfaces inherit the rule.

## r2.1 changes
- States-1 “Public project · media failed”: explicit failure placeholder (`.fig-fail`, warning glyph, “Figure 2 failed to load”, file + cause) with the retained caption “Forecast MAE by horizon”, a Retry button and the long-description link. This is the only place the failed-media treatment appears; normal references show the real chart.
- Board labels: States-1 `r2.1`; States-2 `r2.1 · content inherited from r1`.
