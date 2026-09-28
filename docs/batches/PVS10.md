# PVS10 — Mentor requests and office hours
## Result
Mentors can publish availability/expertise; project members can raise a bounded queue of help requests that mentors claim, organizers can reassign, and claimants resolve with a participant-visible note; mentors/organizers can also schedule capacity-bound office-hours slots participants sign up for.
## Changes
- New `mentorship` app: `MentorProfile` (track expertise, availability), `MentorRequest` (pending→claimed→resolved/cancelled, capped at 5 active per project), `OfficeHourSlot`/`OfficeHourSignup` (capacity-checked signup).
- `mentorship.services`: `create_request`/`claim_request`/`reassign_request`/`resolve_request`/`cancel_request`, `sign_up_for_office_hours`/`cancel_office_hours_signup` — all `select_for_update`, all audited.
- Views split by audience: participants see their own project's requests and office-hours capacity (never other projects' queue or attendee identities); mentors/organizers get the queue and attendee lists. No chat/messaging surface was added.
- Registered `mentorship.mentorprofile`/`mentorrequest`/`officehourslot`/`officehoursignup` in the v2 final-archive schema (the event-owned-model guard flagged the first three; the signup table was added for backup completeness).
## Verification
- `test_mentorship.py` (6 tests, including a real final-archive build/restore round trip with M2M and FK data) → all passing.
- Full suite: 1195 passed/20 skipped. `test_final_archive.py`'s coverage guard passes with the new tables classified.
- `spectacular --validate --fail-on-warn`, `generate_sdks.py` + `--check`, `check_openapi_artifact.py` → clean.
## Limitations
- No UI (PVS-H03). No reminder/notification integration (out of scope per "avoid chat-clone").
## Next
PVS-H02 (realistic load, DB and performance hardening) — Core feature roadmap (through PVS10) is now complete.
