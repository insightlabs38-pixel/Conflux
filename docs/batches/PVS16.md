# PVS16 — Event-operations utility pack
## Result
Organizers can publish an agenda; attendees get a public agenda page, an iCalendar feed, safe livestream embeds, a JSON event-state endpoint, an SVG status badge and a printable expo map.
## Changes
- `onsite.AgendaSession` + organizer CRUD (same-event room/track, https-only stream, audited); registered in the final archive.
- Embed allow-list (YouTube-nocookie, Vimeo, operator hosts), RFC 5545-correct ICS with injection-safe escaping, escaped badge, map restricted to publicly visible projects.
## Verification
- `test_event_logistics.py` (30): CRUD/authz/validation, 10-case embed policy, XSS-escaped page, ICS folding/escaping/injection, phases, badge, map visibility, unpublished → 404.
- Full suite 1319 passed/23 skipped; ruff, OpenAPI + SDK checks clean.
## Limitations
- No UI editor for sessions (API/MCP only); no per-session reminders; feeds are uncached by the publication-window policy.
## Next
PVS17 (operator/participant convenience pack).
