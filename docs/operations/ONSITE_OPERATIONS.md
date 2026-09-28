# Hybrid and in-person operations

All under `.../events/<e>/`; archived events are frozen.

- **RSVP:** participants `GET/PUT my-attendance/` (`in_person`, `remote`, `not_attending`). Staff (volunteer/organizer) `GET attendance/` and `GET onsite-summary/` (RSVP counts, checked-in, projects placed, free slots).
- **Pass and QR:** `GET my-pass/` returns a stateless HMAC-signed pass bound to this event and person (reprint any time, nothing stored); `GET my-pass/qr/` is the same pass as an SVG QR. A volunteer's `POST checkins/scan/ {token}` verifies it, records the existing `ParticipantCheckIn` once (a rescan says `already_checked_in`) and marks a remote RSVP as in person. Forged, tampered, other-event or non-participant passes are refused.
- **Places:** organizers manage `locations/` (`room`, `table`, `booth`; tables and booths may sit in a room; optional `x`/`y` in metres for distance tooling; capacity defaults to 1 for tables/booths). Deleting or resizing a location in use is refused.
- **Placement:** `PUT projects/<p>/location/ {location|null}` (capacity-checked, audited). `POST locations/auto-assign/ {apply, kind}` previews (default) or places unplaced projects that have an in-person member into free slots ordered by track then name. `GET project-locations/`: organizers, volunteers and judges see all; participants only their own project.

Attendance is personal data and joins per-subject export/erasure; locations and placements travel in v2 final archives.
