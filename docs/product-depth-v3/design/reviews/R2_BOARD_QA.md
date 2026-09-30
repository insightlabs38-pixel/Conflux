# R2 board QA ledger
Manual review of every r2 screenshot at full resolution (design lead, r2 pass). The overflow script (`exports/r2/qa/dimension-report.json`) was used only as a first filter; verdicts below come from looking at each PNG.
Method: 19 boards are byte-identical to r1 (MD5 of PNG) and were inspected at full res during the r1 audit; the other 26 were re-inspected after regeneration. Checked per board: blank regions, fixture realism, alignment/rhythm, clipping, truncation, card nesting, radii/borders, hierarchy, primary action, pane balance, text size, status semantics, mobile target size, "mature software at a glance".

## r1 audit findings that drove changes
Under-filled: Shell-Participant, Shell-Judge, MyEvent, Story-Rich/Editor/History, Judge-Review. Real defects the script missed: `.top` bars collapsing to ~30px outside the shell grid (Story-*, Builder-*, Deliberation-Finalize); clipped tables/actions in Deliberation-Finalize and Builder-Plan; map marker over label (Judge-Dialogs); dead strip in Data-Filters; overflow in the index board.

| Board | Artboard | Verdict | Notes |
|---|---|---|---|
| Main | 1440×900 | PASS | Index rewritten for r2 (45 artboards, D13/D14). Board-map rows wrap instead of clipping (r1 status column overflowed by ~90px). |
| Sys-Foundations | 1440×1760 | PASS (r1-identical) | Pixel-identical to r1; inspected at full res. Revision label → r2. |
| Sys-Components | 1440×2540 | PASS | Responsive-rules table rewritten with concrete 768/1024/1440/1800 rules. Known: `.btn` border uses line-2 (1.7:1); button label is the identifier, recorded in D-008. |
| Sys-Directions | 1440×2050 | PASS (r1-identical content) | Exploration record kept as-is; label → r2. |
| Sys-Dark | 1440×1560 | PASS | NEW. Neutrals, semantic ink/tint/line, measured dark contrast table, buttons/inputs/focus, table rows (hover/selected/cursor/edit), status, banners, overlays L0–L2, theme-authority panel. Dark comp exposed 3 real bugs, fixed in v3.css (inherited ink, hard-coded step/count/code colours, flat elevation). |
| Shell-Organizer | 1440×900 | PASS (r1-identical) | Dense, balanced; ~55px slack under "Live judging by track" is panel padding. |
| Shell-Dense | 1440×900 | PASS (r1-identical) | Palette scrim/elevation clear; intentional. |
| Shell-Overlays | 1440×640 | PASS (r1-identical) | Four popover specimens; captions readable. |
| Shell-Participant | 1280×860 | PASS (fixed) | r1 was ~44% blank. Now the ready/frozen participant state at desktop (frozen banner, still-open items, team & project, day timeline, pass, where, help). Reuses D4 patterns, no filler cards. |
| Shell-Judge | 1280×800 | PASS (fixed) | r1 was 3 rows + 1 panel. Now 9-stop route table with route/room, pacing bar with expected marker, drafts, recusal, flag-awaiting-organizer; summary strip kept to 5 figures. |
| Shell-Mobile | 1250×844 | PASS (r1-identical) | Targets ≥44px; sheet scrim intentional. |
| Data-Surface | 1440×1000 | PASS (r1-identical) | Strong reference. Known minor: sticky action column of the cursor row shows a stray hairline fragment at the inspector edge; Changed column is tight at 1440. Wide/1024 refs supersede for other widths. |
| Data-Filters | 1350×1000 | PASS (fixed) | Artboard trimmed from 1440 to 1350: r1 had a ~125px dead strip on the right. |
| MyEvent | 1280×1090 | PASS (fixed) | r1 artboard was 1380 with ~24% empty. Now full page height; fold at ~900 (content scrolls). No modules added. |
| MyEvent-Mobile | 860×1000 | PASS (r1-identical) | Action + ready pair; targets ≥44px. |
| Story-Editor | 1440×960 | PASS (fixed) | Source and preview now continue through Results & benchmark (architecture block, ablation table, citations) and Limitations; scrollbar thumbs show scroll state. Top bar restored to 44px. |
| Story-Rich | 1440×900 | PASS (fixed) | Adds figure+caption, code block, architecture block, citation-heavy paragraph below the benchmark; slash menu opens beside caret; comments/suggestions unchanged. LaTeX popover moved below the equation so it no longer covers text. |
| Story-History | 1440×900 | PASS (fixed) | Diff now shows folded unchanged context, a moved block, Limitations/References hunks (7 changed · 1 moved). Panes clip instead of overlapping footer. |
| Judge-Review | 1440×920 | PASS (fixed) | Evidence pane now a long technical story (summary, key result, method, code, evaluation, limitations) with scroll thumb, "41% read · position kept" chip, and a pinned artifacts/notes dock. Three-pane model untouched. B-06 now Draft to match Shell-Judge. Known: rubric pane has slack below feedback (short rubric, intentional). |
| Judge-Dialogs | 1440×800 | PASS (fixed) | Route-map marker no longer collides with the placeholder label. |
| Judge-Mobile | 1250×844 | PASS (r1-identical) | Task-specific tabs; sticky score bar. |
| Pairwise-Compare | 1440×900 | PASS | NEW. Pair queue | aligned A/B evidence (facts, summary, key result, figures, artifacts) | decision panel. Frozen labels per side, linked scroll, keys A/B/T/S/R/Z/L, one-line criterion focus, adaptive "why this pair", history, progress. Nothing coloured better/worse. |
| Pairwise-States | 1440×950 | PASS | NEW. Six states: choice+undo, tie (and forced-choice disabled reason), conflict/recusal, progress+history, hybrid tiebreak flow, read-only method summary. Fixed an unbalanced div found in first render. |
| Pairwise-Narrow | 1250×844 | PASS | NEW. <768: A / B / Compare tabs, sticky Prefer A/B bar, ⋯ menu, undo. 768–1023 rule stated. |
| Deliberation | 1440×1080 | PASS (r1-identical) | Dense and balanced; inspector void above Approvals is intentional (notes grow downward). |
| Deliberation-Finalize | 1440×900 | PASS (fixed) | r1 middle table/actions were clipped and the preview header overlapped. Columns re-proportioned; added a "what changes for teams" table so the plan step is not a blank column. Top bar 44px. |
| Public-Event | 1280×1700 | PASS (r1-identical) | Full page height; compact hero. |
| Public-Event-Themed | 1280×1100 | PASS (r1-identical) | ~100px reading whitespace above the theme footer is intentional. |
| Public-Event-Mobile | 860×1500 | PASS (r1-identical) | Category chips scroll horizontally by design. |
| Public-Project | 1200×2110 | PASS (r1-identical) | Long-form reading treatment preserved. |
| Public-Project-Mobile | 860×1500 | PASS (r1-identical) | As-judged pane is short by design (snapshot). |
| Builder-Setup | 1440×1180 | PASS (r1-identical) | ~50px bottom slack. |
| Builder-Pages | 1440×920 | PASS (fixed) | Top bar no longer collapses; skeleton preview is deliberate for a not-yet-open event. |
| Builder-Plan | 1440×920 | PASS (fixed) | Checks/Approval text was clipped (nowrap); now wraps. Top bar 44px. |
| Onsite-A | 1250×844 | PASS (r1-identical) | Targets ≥44px. |
| Onsite-B | 1250×844 | PASS (r1-identical) | Targets ≥44px. |
| States-1 | 1440×1770 | PASS | Content identical; revision label → r2. Empty cell space is inherent to the matrix. |
| States-2 | 1440×1560 | PASS | As above. |
| Dark-Organizer | 1440×1000 | PASS | Rail/top bar, inspector, selected rows, nested filters + query, job bar, bulk bar in dark. Derived from Data-Surface markup with data-theme. |
| Dark-Judge | 1440×920 | PASS | Evidence, rubric, warning tint, autosave, disabled submit; primary-on-accent text uses accent-ink (was hard-coded white). |
| Dark-MyEvent | 860×1000 | PASS | Warning/action-needed and ready/success semantics side by side; QR keeps a light quiet zone. |
| Dark-Overlays | 1440×900 | PASS | Scrim, palette with raised surface, focus caret, selection; elevation = lighter layer + edge. |
| Resp-1024 | 1024×768 | PASS | Icon rail 52, docked 340 inspector, two-line name cell, 44px rows, toolbar folds into View, bulk bar keeps one primary. |
| Resp-768 | 1176×1024 | PASS | 768 judge review (evidence | 316 rubric, queue drawer, ≥44px targets) plus drawer specimen and rules. |
| Wide-1920 | 1920×1080 | PASS | 5,012-person fixture: 31 dense rows, 10 columns, wide Team column, inspector fixed at 420, tiny virtual scroll thumb, server-side query, mixed eligibility/check-in/restricted fields, long international names truncated with tooltip. |

## Open items (none block implementation)
- `.btn` default border (line-2) is 1.7:1 light / 1.78:1 dark; the label identifies the control. Owner may choose line-3 buttons (heavier look) — D-008.
- Data-Surface: stray hairline fragment on the cursor row at the inspector edge; Changed column tight at 1440.
- Static comps only: no hover/focus/animation was exercised in a live browser beyond the declared specimens.
- Dark contrast values were computed from token pairs and confirmed visually on the comps; a browser-based axe run belongs to implementation QA.
