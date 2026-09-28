# PVS17 — Operator/participant convenience pack
## Result
Organizers can freeze an event for maintenance, teams can opt out of the public gallery (with organizer override), organizers can preview a CSV import with suggested column mapping, and participants can export their own event data.
## Changes
- `governance.maintenance`: central 503 read-only guard on all event-scoped API writes (organizers exempt), `event.read_only_*` audit.
- `Project.gallery_visible` / `gallery_blocked` feed `public_projects`, so every public surface honours them.
- `csv_preview` (mapping heuristics + row diagnostics) and a self-service subject export reusing the privacy exporter.
## Verification
- `test_convenience_pack.py` (18) incl. a sweep of every event-scoped POST/PUT/PATCH/DELETE route while read-only (none succeeds for a participant); full suite 1337 passed/23 skipped; ruff, OpenAPI, SDK checks clean.
## Limitations
- No UI for these yet; read-only mode does not pause Celery jobs or scheduled publications; award stories omit hidden projects.
## Next
PVS18 only if H02 justified it (it did not) → PVS-H04 release verification. Feature freeze 08:00 UTC Tue.
