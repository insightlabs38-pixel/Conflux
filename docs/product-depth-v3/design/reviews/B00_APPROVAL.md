# PD-DESIGN-B00 approval ledger (implementation review of the r2.1 handoff)
Each section records what was opened and checked against product/domain constraints, what was found, and the disposition. Findings are resolved by a decision in `decisions/` or named as an implementation obligation; none reopens the design. Later tasks of the batch append sections.

## T03 · design/app-shell and design/organizer-data-surface
Opened at full resolution: `Shell-Organizer`, `Data-Surface` (screenshots); loaded in Chromium at 1440 and measured: top bar 44px, rail 216px, inspector 372px, dense rows 28px, fonts Plex Sans/Mono only (matches `VISUAL_CONTRACT.md`). Read: both READMEs, D-002, D-003, D-009, the Shell-Dense/Overlays/Mobile/Participant/Judge and Data-Filters, Resp-1024, Wide-1920 and Dark-Organizer must-preserve lists.

| Check | Result |
|---|---|
| Hierarchy and dominant action | Overview leads with a five-figure summary strip (at most six, each linking to records) and a needs-attention table with one row action each; Data-Surface leads with the saved view and filter chips, bulk bar bottom. Pass. |
| Filtering, nesting, text query | Chips, an ANY OF group, "Add group" and the equivalent query line are drawn. UI depth is 3 (D-003); the server `QUERY` accepts 4 (`core/query.py MAX_DEPTH`), so every UI query is valid. Pass. |
| Selection vs cursor, bulk | 3 selected, "Select all 243", "Frozen snapshot, plan first", at most 4 actions plus More: matches the shipped `BULK_PLAN` planner (plan, approve, apply). Pass. |
| Async operation | Job banner with progress, pause and details; partial-failure retry is specified in D-003 and drawn in Shell-Dense. Pass. |
| Sensitive data | Email masked with a reveal control, diet marked "Restricted, needs Safety role". Obligation O-1. |
| Mutation | "Send reminder", "Mark as signed on paper" are inspector actions. Obligation O-2. |
| Edge and wide states | Resp-1024 docked inspector, Wide-1920 (5,012 rows, 10 columns), Dark-Organizer, narrow row-list plus detail page and mobile nav sheet exist. Pass. |
| Known gaps stated by the design | Board view only named; column resize and reorder handles not drawn; collapse animation not shown. Not required by the task; named in each README. |

### Findings and disposition
- F-1 (P3) D-002 says "at most 6 default rail items per role" but Shell-Organizer and `roleDestinations` show Overview plus seven Manage-event items. Resolved by D-011: the organizer rail follows `roleDestinations` (the board is the reference); the six-item rule applies to the roles that have no Advanced group.
- F-2 (P3) The boards render avatar initials and one count at 10px, below the 11px floor of V-TYPE-2. Resolved by D-011: production uses `--fs-11`.
- F-3 (P3) The `DataGrid` shipped in PD-F002-B01 has arrow/Home/End/Page keys but not the J/K, X, Shift-range, E, V, F shortcuts or `aria-sort` drawn here. This is an implementation obligation for PD-F004, not a design conflict.
- O-1 reveal of a masked value is a server-authorized, audited action (never a client toggle); a restricted column says why it is masked.
- O-2 inspector mutations go through the canonical services with the existing version/idempotency checks (a stale inspector shows the conflict, never overwrites); preview-as stays read-only.

Disposition: **approved for implementation** with D-011 and obligations O-1, O-2, F-3.

## T04 · participant, judge, public, builder and onsite references
Opened at full resolution: `MyEvent`, `Story-Editor`, `Judge-Review`, `Resp-768`, `Deliberation-Finalize`, `Public-Project`, `Builder-Plan`, `Onsite-A`. Read the must-preserve lists of all eight references and D-005, D-006, D-010. `exports/r2.1/qa/dimension-report.json`: 45 boards, none wider than declared; the phone boards are three-phone artboards (390px each, 1250px wide), so narrow behavior is judged on the phone frames, not the artboard.

| Reference | Domain check against the shipped system | Result |
|---|---|---|
| participant-my-event | One primary per "Do next" row; hub derives from canonical state; the frozen revision is named; pass has offline save and a manual fallback in its README | Pass |
| project-story-editor | Blocking vs advisory preflight; completeness 78% is 7 of 9 required items (deterministic); "Public render, renderer 2.3.1" matches the frozen-preview renderer version; Mermaid shown as server-rendered output | Pass, O-4 |
| judge-review | Weights 30+25+25+20 = 100; submit disabled with reason; recusal and flag always reachable; frozen r3 evidence tag; offline buffer and narrow layout (Resp-768, Judge-Mobile) | Pass |
| deliberation-awards | Frozen inputs listed, override needs category and written reason, proposer cannot approve, plan, approve, preview, apply, immutable receipt: same shape as the `APPROVAL` primitive | Pass, F-5 |
| public-event, public-project | Scores and judge comments not public; living vs "as judged r3" with banner and provenance; reading column, figures with alt text and long description; theme limited to accent and background with a contrast gate | Pass |
| event-builder | Plan is the same engine as the CLI and Event-as-Code (diff parity drawn); stale plan "valid until, re-validate"; data-leaves-platform needs co-organizer approval; https-only endpoint, vault ref for the secret, test sends no real data | Pass |
| onsite-mobile | One dominant action of 56px or more, offline-safe desk, full-screen offline pass, manual code fallback in the README | Pass, O-3 |

### Findings and disposition
- F-4 (P3) the three-phone artboards are wider than any phone; the dimension report is clean, so this is presentation only. No action.
- F-5 (P3) the finalization board says "2 of 3 (override)", "1 of 2 approvals" and "needs 2 approvals" in three places. Meaning: two of the three eligible approvers must approve an override. Implementation uses one stated rule from the policy, drawn from `APPROVAL`; copy is adaptable.
- O-3 whether a missing waiver blocks check-in (Onsite-A allows it with a warning, Data-Surface says "insurance requires it by 17:00") is event policy decided by the server; the UI shows the server verdict and never decides eligibility.
- O-4 story, figure, diagram and math content is untrusted: rendering goes through `core/rich.py` and its sanitizer, public pages use the same output, alt text is required by the preflight, never trusted from the client.

Disposition: **approved for implementation** with F-5, O-3, O-4.
