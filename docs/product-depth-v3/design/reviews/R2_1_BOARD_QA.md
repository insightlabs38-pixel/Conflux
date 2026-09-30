# r2.1 board QA ledger
**What was opened**: all 45 current r2.1 boards, opened in this session (2026-09-30) at 1× device scale from the final r2.1 build. Boards taller than 1000px were opened as consecutive 1000px full-width tiles; Wide-1920 was opened as left/right halves. Nothing was accepted on the strength of an earlier pass or a byte-identical file. Boards whose source changed after their first viewing were re-opened after the final rebuild; fine-detail fixes (Data-Surface row edge, Sys-Components table, Deliberation input, States-1 media tile, top-bar action rows) were also checked in 1.5–8× zoomed crops.
**Checked per board**: alignment, whitespace, clipping, action hierarchy, control baselines, fixture realism, pane balance, truncation, responsive composition, dark tokens, status semantics.
**Result**: 45 opened · 23 FIXED · 22 PASS · 0 BLOCKED. The dimension/overflow script (`exports/r2.1/qa/dimension-report.json`) was only a first filter; the remaining flags there are content inside intentionally clipped scroll panes and a ≤20px bottom padding (unchanged from r2).
**Global change**: every board with an outlined button now renders the `line-3` border (D-008); that alone is not counted as FIXED.

| Board | Artboard | Verdict | Note |
|---|---|---|---|
| Main | 1440×900 | FIXED | Label r2.1 / frozen for implementation; density line matches D-009. |
| Sys-Foundations | 1440×1760 | FIXED | Label `r2.1 · content inherited from r1`; spacing token labels no longer wrap (60→76px); missing ⓘ glyph replaced by the info icon. |
| Sys-Components | 1440×2540 | FIXED | Label r2.1; button grammar states line-3 border, ghost/text, segmented, tag and disabled rules. Table hairlines reach the row end. |
| Sys-Directions | 1440×2050 | FIXED | Label only: `r2.1 · exploration record from r1`. Wireframe thumbnails are intentional. |
| Shell-Organizer | 1440×900 | PASS | Line-3 row buttons read clearly, not heavy. ~55px under “Live judging” is panel padding. |
| Shell-Dense | 1440×900 | PASS | Palette/scrim/elevation clear. |
| Shell-Overlays | 1440×640 | PASS | Four specimens, captions readable. |
| Shell-Participant | 1280×860 | PASS | Ready state; banner/row actions aligned. |
| Shell-Judge | 1280×800 | PASS | Modest bottom slack; right column is growth space. |
| Shell-Mobile | 1250×844 | FIXED | Organizer phone listed 4 items under “Needs attention · 7” → all 7 shown; participant “Later today” completed (13:00–20:30). |
| Data-Surface | 1440×1000 | FIXED | Stray “…” at the inspector edge removed (row-action overflow + ellipsis); hairlines reach the inspector on every row; Changed 80→96px with Team still untruncated. |
| Data-Filters | 1350×1000 | PASS | Popovers balanced; dialog footers aligned. |
| MyEvent | 1280×1090 | PASS | Event-pass (Save offline / Add to Wallet) and help (button + Emergency link) rows aligned; full page height. |
| MyEvent-Mobile | 860×1000 | PASS | Targets ≥44px. |
| Story-Editor | 1440×960 | FIXED | Figure 2 is a real chart; caption + Markdown source say “Forecast MAE by horizon”. Top controls (segmented ×2, History, Comments, primary) aligned. |
| Story-Rich | 1440×900 | FIXED | Figure 2 real chart + renamed caption; slash menu overlap is the intended state. |
| Story-History | 1440×900 | FIXED | Diff now records the caption rename (judged r3 old wording, living r7 new). |
| Judge-Review | 1440×920 | FIXED | Figure 2 real chart beside the key-result table; rubric slack is intentional (short rubric). |
| Judge-Dialogs | 1440×800 | PASS | Dialog footers aligned; floor-plan placeholder is a map, not a figure. |
| Judge-Mobile | 1250×844 | FIXED | Figure 2 real chart at phone width. |
| Deliberation | 1440×1080 | FIXED | “Add note” input reserved icon padding with no icon → icon added. Inspector void above Approvals is growth space. |
| Deliberation-Finalize | 1440×900 | PASS | Approval/footer row aligned; disabled Apply visibly distinct. |
| Public-Event | 1280×1700 | PASS | Card art placeholders are labelled image slots (thumbnails), not figures. |
| Public-Event-Themed | 1280×1000 | FIXED | Artboard 1100→1000 (≈180px slack above the theme strip); remaining gap is reading space. |
| Public-Event-Mobile | 860×1420 | FIXED | Text-only rows no longer forced to 88px; themed phone mirrors desktop (Last year’s projects, secondary action); footers; 1500→1420. |
| Public-Project | 1200×2010 | FIXED | Figure 1 real architecture diagram; Figure 2 real chart; 2110→2010. |
| Public-Project-Mobile | 860×1600 | FIXED | Vertical architecture diagram; Figure 2 + Limitations from desktop; 1500→1600 (page height). As-judged phone short by design. |
| Builder-Setup | 1440×1180 | PASS | Right column below preview is inspector growth space. |
| Builder-Pages | 1440×920 | PASS | Skeleton preview deliberate (event not open). |
| Builder-Plan | 1440×920 | PASS | Top group (segmented, Validate, Apply) aligned; Checks/Approval wrap cleanly. |
| Onsite-A | 1250×844 | PASS | Targets ≥44px. |
| Onsite-B | 1250×844 | PASS | Targets ≥44px; segmented Available/Break aligned. |
| States-1 | 1440×1770 | FIXED | Label r2.1; media-failed tile uses explicit failure placeholder + retained caption “Forecast MAE by horizon” + Retry + long description. |
| States-2 | 1440×1560 | FIXED | Label only: `r2.1 · content inherited from r1`. Cell space is inherent to the matrix. |
| Dark-Judge | 1440×920 | FIXED | Figure 2 real chart; tokens read correctly in dark. |
| Dark-MyEvent | 860×1000 | PASS | Warning vs success semantics; QR quiet zone light. |
| Dark-Organizer | 1440×1000 | FIXED | Shares Data-Surface column and row-action fixes. |
| Dark-Overlays | 1440×900 | PASS | Scrim, raised palette, focus caret. |
| Sys-Dark | 1440×1560 | FIXED | Label `r2.1 · dark`. Buttons show line-3 in dark. |
| Resp-1024 | 1024×768 | PASS | Docked inspector, folded toolbar; bulk bar keeps one primary. |
| Wide-1920 | 1920×1080 | PASS | 5,012-person fixture; Dense shown as a user choice (consistent with D-009). |
| Resp-768 | 1176×1024 | FIXED | Figure 2 real chart; footer (outlined ×3 + ghost Notes) and Flag/Recuse rows aligned. |
| Pairwise-Compare | 1440×900 | PASS | A/B method figures stay neutral placeholders on purpose (drawing only A would unbalance the pair). |
| Pairwise-Narrow | 1250×844 | FIXED | Figure 2 real chart; third phone’s decision bar gets its status line so all bars match. |
| Pairwise-States | 1440×950 | PASS | Configured tie cap/strength shown as values, not policy (D-010). |

## Button/control alignment sweep
Audited: Story editor top controls, Builder-Plan top group, Deliberation-Finalize approval/footer, My Event pass/help, Resp-768 evidence/footer, Pairwise-Narrow decision bars, Judge-Dialogs / Shell-Overlays / Data-Filters dialogs, Dark-Overlays / Sys-Dark. No baseline or height offset was found in `.btn`, segmented controls, text links or tags; outlined, ghost, text-link, tag and segmented controls stay visually distinct. Only change: Pairwise-Narrow bar heights made consistent.

## Remaining limitations (non-blocking)
- Static comps: hover/focus/animation not exercised in a live browser beyond drawn specimens; axe/browser contrast runs belong to implementation QA.
- Figures are design fixtures (inline SVG from the fixture table); the 95 % CI band widths are illustrative.
