# PD-B04 — Frontend routing, server-state and typed-client foundation
## Result
All 8 tasks DONE. Nested routing, a server-state layer, the generated typed client as the only transport, URL-state, async-operation and realtime contracts, and the major workspaces migrated onto them with no backend change.
## Changes
- Router with 11 legacy URL redirects; `useLoad`/queries per session (reset on sign-in/out); `apiRequest` via `@conflux/sdk`, raw `fetch` ratcheted out; event/stage/plan in the URL (`useUrlParam`).
- `useOperation` (evidence upload) and a polling realtime hub (inbox); effect-based fetching 34 → 17 files, each remaining one recorded and ratcheted.
- T08 regression `route-drafts.spec.ts`: drafts, deep links, refresh, Back/Forward and role change across participant, organizer and judge on real fixtures.
## Verification
- `make verify-fast` on final main: pytest 1454/23 skipped, web 294 + embed 8, ruff, prettier, tsc, build, OpenAPI and SDK checks clean
- `make e2e-fast`: read-only 107 passed, isolated-mutation and canary ok; route-drafts 36/36 over six concurrent fresh fixtures
- `validate_queue.py` valid; matrix `docs/verification/PD-B04/MATRIX.md` has a proof per capability
## Findings
- P1 fixed (ESC-20260930-001): offline judge outbox/cache were keyed by plan only, replaying one judge's ballots as the next judge on a shared browser; now per account. Legacy unscoped entries are left untouched (owner may prefer adoption or a prompt).
## Limitations
- Panel-internal selection state (judge project, builder item, tabs) is not in the URL; 17 files keep effect fetching for recorded reasons; PostgreSQL run not repeated (no backend change).
- Same agent implemented and reviewed; no T90/T91/T95 tasks exist for this batch.
## Next
PD-F001-B01. Checkpoint: `checkpoints/CP-PD-B04.yaml`.
