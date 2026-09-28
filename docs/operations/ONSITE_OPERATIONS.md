# Hybrid and in-person operations

All under `.../events/<e>/`; archived events are frozen.

- **RSVP:** participants `GET/PUT my-attendance/` (`in_person`, `remote`, `not_attending`). Staff (volunteer/organizer) `GET attendance/` and `GET onsite-summary/` (RSVP counts, checked-in, projects placed, free slots).
- **Pass and QR:** `GET my-pass/` returns a stateless HMAC-signed pass bound to this event and person (reprint any time, nothing stored); `GET my-pass/qr/` is the same pass as an SVG QR. A volunteer's `POST checkins/scan/ {token}` verifies it, records the existing `ParticipantCheckIn` once (a rescan says `already_checked_in`) and marks a remote RSVP as in person. Forged, tampered, other-event or non-participant passes are refused.
- **Places:** organizers manage `locations/` (`room`, `table`, `booth`; tables and booths may sit in a room; optional `x`/`y` in metres for distance tooling; capacity defaults to 1 for tables/booths). Deleting or resizing a location in use is refused.
- **Placement:** `PUT projects/<p>/location/ {location|null}` (capacity-checked, audited). `POST locations/auto-assign/ {apply, kind}` previews (default) or places unplaced projects that have an in-person member into free slots ordered by track then name. `GET project-locations/`: organizers, volunteers and judges see all; participants only their own project.

Attendance is personal data and joins per-subject export/erasure; locations and placements travel in v2 final archives.

## Judge routes

`GET .../stages/<s>/evaluation-plans/<p>/my-route/` (judge) and `.../routes/` (organizer, every pool judge plus totals) order the projects a judge is already expected to evaluate by walking distance. Candidates come from the same rule the judging queue uses (`evaluations.candidates.judge_candidates`): pool membership, the active assignment version, the judge's conflicts and project eligibility. Routing never adds, removes or reassigns anything.

Only projects placed at a table or booth are routed; the rest are listed as `unplaced`. By default only projects the judge has not yet evaluated are included (`remaining_only=false` shows all). `start=<location>` fixes the entrance. Distance is Euclidean on `x`/`y` plus a 15 m penalty for changing rooms; without coordinates it falls back to 5 (same room) or 30 (different rooms). Up to 9 stops are solved exactly, more with nearest-neighbour plus 2-opt; both are deterministic. Each route reports `total_distance` against a `baseline_distance` (name order).
