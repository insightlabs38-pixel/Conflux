# PVS-H05 — Final demo-readiness package
## Result
A one-command, repeatable demo (`make demo-reset`) produces a rich deterministic event; `make demo-e2e` regenerates screenshots and clips and doubles as a pre-recording smoke test; a runbook documents the script, accounts and recovery.
## Changes
- `scripts/demo-reset` + `demo_showcase` (landing blocks, agenda, expo placements, rules + acknowledgements, continuations, announcement), idempotent and purge-safe; Makefile targets.
- Fixes found while capturing scenes: agenda times were shown in the server timezone but labeled UTC; agenda/map/embed/print styles; anchor buttons underlined.
- Playwright scenes extended (agenda, expo map, API explorer, sign-in).
## Verification
- `test_demo_showcase.py` (idempotent, deterministic, purgeable); agenda-UTC regression; Playwright 37/37 on the reset stack; evidence refreshed in `docs/verification/PVS-H04/` and `docs/verification/PVS-H05/`.
## Limitations
- Public IDs change per reset (content is deterministic); the demo event is closed, not live; no UI for PVS features (see runbook).
## Next
Campaign complete; stop autonomous work.
