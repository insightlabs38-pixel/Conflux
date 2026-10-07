# Canonical UI state matrix — v1 (design revision r2.1)
Frozen by PD-DESIGN-B00-T05. Rules come from `html/States-1.html` and `html/States-2.html` (screenshots beside them); this page maps every reference surface to every state class so a task can see what it must build. A UI task implements its row, not only the normal state. A surface that does not have a class says why.

## Rules (ids are citable)
| Id | State | Rule (board cell) |
|---|---|---|
| S-NORMAL | Normal | One primary action per context; status is icon plus word; live data shows its age (Normal · grid, My Event, judge autosave) |
| S-LOAD | Loading | Skeleton only when the layout is predictable, headers and toolbar stay live; unknown fields use a spinner and text; after 8s say what is slow and offer Cancel or Keep working |
| S-EMPTY | Empty | Say why it is empty, offer the one next action, tell "no data" from "no matches" and name the filters that hid everything (Empty · grid, first run, queue complete) |
| S-PART | Partial | Show what loaded, isolate the failure to the smallest region, retry that region only, never imply completeness (one column failed, coverage gap, media failed) |
| S-ERR | Error | Say whether data was kept, what retry does, show a mono error reference; partial success names the parts (page load, save failed with draft kept, bulk 231 sent and 12 failed) |
| S-DENY | Permission denied | Name the missing role or scope and who can grant it; hide what must not be discoverable, mask what may be known; the server is the authority and the UI mirrors it; a disabled action states its reason as text |
| S-VALID | Validation | Inline on the field and a summary at the top, say how to fix, focus the first error, nothing is lost; blockers list what and where, warnings never block |
| S-LARGE | Large and dense | Virtualize, total count always visible, server-side sort and filter, truncate with tooltip and never wrap, sticky header and first column, every heat matrix has a table twin |
| S-DEST | Destructive and high impact | Neutral until the last step, the final button is the only red, state scope, count and reversibility; undo toast for reversible, typed confirmation only for irreversible, plan then approve then apply for publication |
| S-MOBILE | Mobile | Row list with title, one status and two fields; filters and views in a bottom sheet; detail page instead of inspector; bulk bar pinned to the bottom; targets at least 44px |
| S-OFF | Offline and degraded | Say what still works and what is queued, never lose input and show the pending count; live surfaces show connection health and data age; actions that need live data are disabled with a reason |

## Coverage by reference surface
Cell = where the state is drawn (board cell or reference board) or the rule it inherits. "n/a" is a reasoned absence.
| Surface | Normal | Loading | Empty | Partial | Error | Denied | Valid. | Large | Destructive | Mobile | Offline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| app-shell, switcher, palette | Shell-* | S-LOAD | S-EMPTY | S-PART | S-ERR | Shell-Overlays preview-as, States-1 route | n/a | Wide-1920 | n/a | Shell-Mobile | States-2 live ops |
| organizer-data-surface | Data-Surface | States-1 grid, inspector | States-1 filters match nothing | States-1 one column | States-1 page, bulk job | States-1 masked column | States-2 inline edit | States-2 5,012 rows, Wide-1920 | States-2 undo toast, Data-Filters bulk plan | States-2 grid list, sheet, detail | States-2 live ops |
| participant-my-event | MyEvent | S-LOAD | States-1 first run | S-PART | S-ERR | S-DENY | States-2 form | n/a | Judge-Dialogs withdraw | MyEvent-Mobile | States-2 pass offline |
| project-story-editor | Story-Editor | S-LOAD | S-EMPTY | S-PART | States-1 save failed | S-DENY | States-2 preflight | Story-History | S-DEST | S-MOBILE | States-1 save failed, draft kept |
| judge-review | Judge-Review | S-LOAD | States-1 queue complete | S-PART | S-ERR | Judge-Dialogs recusal | submit disabled with reason | Pairwise-States | Judge-Dialogs | Judge-Mobile, Resp-768 | States-2 judge offline |
| deliberation-awards | Deliberation | S-LOAD | S-EMPTY | States-1 coverage gap | S-ERR | States-1 disabled with reason | Deliberation-Finalize override | States-2 24 x 40 matrix | States-2 publish, Deliberation-Finalize | S-MOBILE | S-OFF |
| public-event, public-project | Public-* | S-LOAD | S-EMPTY | States-1 media failed | S-ERR | S-DENY | n/a | S-LARGE | n/a | Public-*-Mobile | service worker caches the page, S-OFF |
| event-builder | Builder-* | S-LOAD | S-EMPTY | S-PART | S-ERR | S-DENY | Builder-Plan https error, diagnostics rail | S-LARGE | States-2 delete event, Builder-Plan apply | S-MOBILE | S-OFF |
| onsite-mobile | Onsite-A | S-LOAD | S-EMPTY | S-PART | S-ERR | S-DENY | manual code fallback | S-LARGE | Undo on check-in | Onsite-A, Onsite-B | Onsite-B pass, States-2 |

## Obligations (implementation)
- The shipped `LoadingState`, `EmptyState`, `ErrorState`, `DeniedState` take a label or a message only. The visual foundation (PD-F004) extends them with the matrix fields: whether data was kept, retry scope, error reference, next action, reason text, cancel after 8s. Every state class stays one shared component, never a per-feature copy.
- Error and denied text comes from the server problem payload (reference, missing role), never composed in the client from a status code alone.
- Dark theme has no separate state boards: states use the semantic tokens, so Dark-Organizer and Dark-Overlays are the evidence.
