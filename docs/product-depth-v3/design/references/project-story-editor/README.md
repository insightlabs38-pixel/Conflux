# Project story editor — design/project-story-editor (r2.1)
**Boards**: Story-Editor (split), Story-Rich (WYSIWYM + comments/suggestions), Story-History (diff, judged vs living)
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Source/Split/Rich share one document model; exact Public/Judge/Frozen preview switch; structured sections with required/recommended and visibility; metadata cards (repo/demo/dataset/paper/model/license); preflight with blocking vs advisory; autosave state; comments anchored to block IDs; suggestions accept/reject; immutable revisions; judged r3 vs living diff.

## Adaptable implementation details
- Toolbar contents, slash menu items, exact lint rule set (event-configurable).

## Keyboard / focus / a11y
- Editor is a labelled textbox/contenteditable with accessible toolbar; alt-text and heading lint; math has text alternative.

## Known limitations
- Real-time cursors and mermaid/diagram rendering are not drawn.

## r2 changes
- Longer technical fixture: Story-Editor and Story-Rich continue through figure+caption, code, architecture block, ablation table, citation-heavy paragraph and Limitations; Story-History shows folded unchanged context, a moved block and reference hunks. Comments/suggestions behaviour unchanged. Scroll thumbs indicate that the panes scroll.
- Must preserve (added): semantic blocks (benchmark, architecture) render the same in rich, split and public views; diff is by block ID with "moved" shown separately from add/delete.
- Known limitations: no live collaborative cursors (deferred); dark not comped for this surface.

## r2.1 changes
- Story-Editor, Story-Rich: Figure 2 renders as a real inline chart; caption and Markdown source now say “Forecast MAE by horizon”.
- Story-History: the diff now shows the caption rename (− “Error by horizon” in judged r3, + “Forecast MAE by horizon” in living r7).
- All outlined buttons now use the `line-3` border (D-008); no layout change.
