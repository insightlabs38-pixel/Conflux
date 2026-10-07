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
