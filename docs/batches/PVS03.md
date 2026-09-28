# PVS03 — Hybrid/in-person event operations
## Result
RSVP, signed QR passes with volunteer scan check-in, and room/table/booth placement with capacity-checked auto-assignment.
## Changes
- New `onsite` app (attendance, locations with optional coordinates, project placement); adds `segno` (pure-Python QR); reuses `ParticipantCheckIn`.
- Placement visibility is role-scoped; attendance joins the privacy export/erasure path; layout is archived.
## Verification
- `test_onsite.py` → 7 passed (authz, capacity/moves, pass forgery/replay, deterministic auto-assign, archived freeze); QR SVG decoded back to its pass in headless Chromium with jsQR.
## Limitations
- API only; printable maps/pass UI in PVS16/PVS-H03.
- Footage unaffected: no public surface changes.
## Next
PVS04.
