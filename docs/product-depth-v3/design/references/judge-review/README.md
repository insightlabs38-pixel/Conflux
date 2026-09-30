# Judge review — design/judge-review (r2.1)
**Boards**: Judge-Review, Judge-Dialogs (recusal, flag, route, offline/conflict), Judge-Mobile, **Pairwise-Compare, Pairwise-States, Pairwise-Narrow**
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Queue | evidence | rubric; frozen-evidence tag; pinned autosave state; recusal + flag always reachable; submit disabled until complete with reason; keyboard scoring (1–5, Tab, ⌘↵, J/K, F, R); pacing indicator; route/current stop; offline buffer with deterministic reconcile.

## Adaptable implementation details
- Rubric anchor display (inline vs popover); queue sort options.

## Keyboard / focus / a11y
- Score scales are radiogroups; unscored criterion highlighted with text; shortcuts are discoverable and disable-able.

## Known limitations
- (r1) Pairwise mode was not designed — resolved in r2, see below.

## r2 changes
**New boards**: Pairwise-Compare, Pairwise-States, Pairwise-Narrow. Judge-Review evidence pane now uses a long technical fixture (scrolls; pinned artifacts + notes dock; "position kept" chip). Judge-Dialogs route-map marker fixed. Narrow tablet (768) and dark variants: `../responsive-wide/Resp-768`, `../dark-mode/Dark-Judge`.

### Pairwise judging — must preserve
- **Layout**: pair queue (248) | aligned A/B evidence | decision panel (352). Evidence is *aligned by section* (facts, summary, key result, figures, artifacts) with linked scroll (L), sticky A/B headers and a per-pair remembered position — comparing must be faster than opening two project pages.
- **Frozen labels** on each side (each project's own judged revision + freeze time). Nothing is coloured better/worse; A/B order is randomised per judge and never implies a ranking.
- **Decision**: A / B always; "Can't separate (tie)" only when configured (share cap shown; disabled with a visible reason when the event forces a choice); Skip reassigns; Recuse from A or B replaces the pair and dependent pairs. One key press saves and auto-advances with 10 s undo; reduced motion → press ↵ for next.
- **Criterion context** is one line ("Overall merit · anchors ▸"), never two full rubrics. Optional one-line reason, visible to organizers only.
- **Progress**: "12 of 40" with adaptive range (34–46), pace, coverage, last decisions editable until judging closes, "why this pair?" one-sentence explanation.
- **Hybrid events**: rubric first; close calls (Δ ≤ configured threshold after normalization) create a tiebreak round of pairs; rubric scores of A/B are hidden during tiebreak; result feeds only the tiebreaker row in Deliberation and never rewrites rubric scores.
- **Keyboard**: A B T S R Z L, [ ] section, J K scroll both.
- **Narrow**: <768 A / B / Compare tabs with sticky Prefer A/B bar and ⋯ (tie, skip, recuse); 768–1023 keeps two columns with the decision bar docked at the bottom.

### Adaptable
- Strength-of-preference chips (off by default, shown only if configured); exact tie-share cap; where "why this pair?" lives.

### Known limitations
- Sync-scroll behaviour, adaptive pair-selection algorithm and Bradley–Terry maths are specified in prose, not drawn. Wide/tablet pairwise layouts other than 768 rules are not comped.

## r2.1 changes
- Judge-Review, Judge-Mobile, Pairwise-Narrow: striped “Figure 2 · Error by horizon” placeholder replaced by a real inline chart titled **Forecast MAE by horizon** (fixture values h=1/6/24, direct labels, Northwind band = 95 % CI). “Error” no longer reads as a render failure; the failed-media state lives only in the state matrix.
- Pairwise-Narrow: the third phone’s decision bar gains its status line so all three bars share one height.
- Pairwise-Compare keeps both method figures as neutral placeholders on purpose — drawing only side A would make the pair look unequal.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
