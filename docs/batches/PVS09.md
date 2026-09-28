# PVS09 — Sponsor challenge and developer resource center
## Result
Sponsors and organizers can attach structured challenge content (API docs, starter repos, contacts, FAQ, workshop references) to an award, and participants get a read-only view of sponsor challenges that reuses eligibility/prize data without leaking sponsor-portal internals.
## Changes
- `awards.AwardResource` model (kind-gated URL/body requirement) + `sponsor_portal.SponsorPortalResourceListView`/`SponsorPortalResourceDetailView`: organizer or the award's own `sponsor_contacts` only (reuses the existing `ensure_can_manage` boundary from fulfillments).
- `awards.ChallengeListView` (`.../challenges/`, workspace-member-only): sponsored awards' name/track/prize components/resources, with `sponsor_contacts`/`eligible_projects`/`judges` deliberately excluded.
- `award_data()` now includes `resources`, reused by the organizer, sponsor-portal and public award views.
## Verification
- `test_sponsor_resources.py` (new, 4 tests) + `test_sponsor_portal.py` → all passing.
- Full suite: 1189 passed/20 skipped. `test_final_archive.py`'s event-owned-model guard passes unchanged (`AwardResource` has no direct FK to `Event`).
- `spectacular --validate --fail-on-warn`, `generate_sdks.py` + `--check`, `check_openapi_artifact.py` → clean.
## Limitations
- `AwardResource` is not yet in the final-archive/event-as-code table set — a reversible scope call to avoid touching the frozen v2 archive contract this late; flag for PVS-H04 if full portability of sponsor content is required.
- No UI (PVS-H03).
## Next
PVS10 (mentor requests and office hours).
