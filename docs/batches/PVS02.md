# PVS02 — Judge deliberation + winner finalization room
## Result
Panel judges can deliberate per award with evaluation-gated visibility, and organizers finalize winners with the panel's tally recorded as evidence.
## Changes
- New `deliberation` app: rooms, notes, stances, quorum/recommendation tally, audited close/finalize.
- `select_winner` accepts extra evidence; winners keep deliberation evidence; archives remap it on reconstruction.
## Verification
- `test_deliberation.py` → 7 passed (authz, panel isolation, no score leakage, tally, override rules, ineligible exclusion); final-archive round trip extended.
## Limitations
- API only (UI in PVS-H03 if time); pairwise panels count any comparison as evaluation of both projects.
- Footage unaffected: no public surface changes.
## Next
PVS03.
