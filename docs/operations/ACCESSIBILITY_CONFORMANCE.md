# Accessibility conformance evidence

`GET /api/v1/workspaces/<w>/events/<e>/accessibility-conformance/` (organizer only) or
`python src/api/manage.py accessibility_conformance <event_public_id>` fetches the public pages
through the real request stack (so publication windows apply) and runs static WCAG 2.1 checks.

Pages: event landing, gallery, results, finalists, and up to 10 project pages, award stories and
project stories. A page a visitor cannot reach (for example unreleased finalists) is reported
`unavailable` with its HTTP status, never audited or counted as passing.

Per page the report carries the SHA-256 of the served content (CSRF tokens excluded), so evidence
is tied to exactly what was audited, and per check: WCAG criterion, level, pass/fail and up to five
evidence snippets. Checks: language, title, single h1, heading order, main landmark and skip link,
image alternatives, link names, control labels, button names, frame titles, zoom, positive tabindex,
duplicate ids, table headers. The composed page theme's contrast is included.

`conformance_claimed` is always `false`. `manual_review` lists what static checks cannot settle
(media alternatives, reflow, focus visibility, keyboard traps, status announcements). Attach human
or assistive-technology results to those items before making any conformance statement.
