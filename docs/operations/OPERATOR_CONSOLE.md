# Workspace operator console

`GET /api/v1/workspaces/<workspace>/operator-console/` requires an organizer
or admin membership. It reads existing event launch checklists, saved event
templates, and workspace audit events without storing a duplicate summary.
The organizer dashboard shows the same data and links each event to its
canonical and signed archive exports.

`health` is launch readiness, using the same rules as the event operations
checklist. It is not a runtime uptime or incident signal. The response shows
the 50 most recently updated events, first 50 templates, and 20 newest audit
events, with total counts for events and templates. Audit entries include
workspace activity by any actor, not only organizers. A refresh fetches the
current state; there is no live subscription or historical health series.
