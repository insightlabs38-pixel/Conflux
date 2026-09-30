# Responsive & wide — design/responsive-wide (r2.1)
**Boards**: Resp-1024 (organizer data surface), Resp-768 (judge review + queue-drawer specimen), Wide-1920 (organizer data surface at 1920×1080 with a 5,012-person fixture)
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Breakpoint rules (authoritative; see D-009)
| Width | Shell | Inspector | Grid | Toolbar |
|---|---|---|---|---|
| ≥1800 | rail 216 | 420, never stretched | more columns + wider values; Dense suggested once | full, one row + chips row |
| 1440–1799 | rail 216 | 372–420 | default columns | full |
| 1024–1439 | rail 52 icons (labels via tooltip) | **docked push**, 340–380 | priority columns; name cell becomes name + team; 44px rows on touch | secondary controls fold into **View**; chips row kept |
| 768–1023 | top bar + drawer nav | full-height sheet | sticky name column, horizontal scroll | search + Filters + View |
| <768 | bottom nav | detail page | row list | filters sheet |
Two-pane workflows (judge): 768–1023 keeps evidence + rubric (316) and moves the queue into a drawer; <768 becomes tabs.

## Must preserve
- Bulk bar keeps exactly one primary action at every width; frozen-snapshot cue stays.
- Wide displays add information, not chrome: no second contextual region on the data surface (it would just repeat the 1440 layout); Ops mode may add one, undocumented here.
- Wide-1920 virtualization cues: row window, tiny thumb, server-side sort/query, "select all N" on the filtered set.
- Touch targets ≥44px from 1024 down; density (comfortable/standard/dense) stays a per-user setting.

## Density recommendation for wide displays
Keep **Standard** as the account default; at ≥1800 wide **offer Dense once** (dismissible, per-user) because 28px rows show ~31 rows at 1080p versus ~24. Never auto-switch density from viewport alone.

## Large-fixture stress test (Wide-1920)
5,012 people / 1,284 teams / 1,041 projects / 9 tracks: long international names and team names truncate with tooltip; mixed eligibility (eligible, student proof, ineligible), check-in states, restricted dietary field, running bulk job with bounce count.

## Known limitations
- 1024 comp shows the inspector-open state only; inspector-closed adds the hidden columns. No 1920 second pane. Pairwise at 1024 is not comped.

## r2.1 changes
- Resp-768: Figure 2 is the real “Forecast MAE by horizon” chart; evidence/footer action rows audited — aligned.
- Resp-1024 and Wide-1920 inherit the row-action cell fix.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
