# PVS15 — Post-event project continuation
## Result
Projects that finalized a submission can, once their event closes, publish an opt-in continuation profile and a short update log; organizers can hide and restore profiles, and public events list the visible ones.
## Changes
- New `continuation` app (`ProjectContinuation`, append-only `ContinuationUpdate`, ≤ 20 updates), all mutations `select_for_update` + audited.
- Validation: http/https URLs without embedded credentials, closed vocabulary for `seeking`, control-character rejection, event-closed and finalized-submission preconditions.
- Moderation persists across member edits; public output omits private/moderation fields; tables registered in the final archive.
## Verification
- `test_continuation.py` (18): lifecycle gates, membership/404 isolation, 11 malformed-input cases, append-only/bounded updates, public visibility, moderation, archive round trip.
- Full suite, ruff, OpenAPI + SDK checks clean.
## Limitations
- No UI (PVS-H03); no notifications or contact channel by design.
## Next
PVS-H03 (frontend/UX/accessibility hardening plus deterministic Playwright scenes/clips).
