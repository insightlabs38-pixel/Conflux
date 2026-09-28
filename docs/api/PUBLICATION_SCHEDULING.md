# Publication scheduling

Organizers/admins manage event-scoped visibility windows at
`/api/v1/workspaces/{workspace}/events/{event}/publication-schedules/` (GET list).
PUT or DELETE `.../{surface}/`, where surface is `gallery`, `finalists`,
`feedback`, `winners`, or `archive`. PUT replaces the complete window:

```json
{"opens_at":"2026-10-01T12:00:00Z","closes_at":null,"finalist_stage":null}
```

Times require an explicit UTC offset and are normalized to UTC. Visibility is
`opens_at <= now < closes_at`; a null closing time means no expiry. Windows are
checked on every read, with no worker, automatic publication mutation, or cron
dependency. Schedule writes/removals are atomic and audited. Archived events
allow schedule management so their existing public archive can be released.

- Gallery gates HTML, landing blocks, public JSON/embed/search/saved searches,
  project detail pages, and the project content used by result stories/cards.
- Winners gates published award reads, landing results, stories and cards;
  it does not select winners or publish awards. Existing award eligibility and
  publication rules still apply.
- Feedback additionally requires the plan's explicit participant release flag;
  project membership/anonymity remain enforced. Organizers retain review access.
- Archive gates all public event reads when the event status is `archived`;
  it does not change event status, `is_public`, or an open/closed event's visibility.
- Finalists requires `finalist_stage` to identify a stage in this event. GET
  `/api/v1/events/{event}/finalists/` or `/e/{event}/finalists/` lists projects
  with finalized submissions in that stage, within the gallery window.
  No ranking, nominations, or advancement state is inferred.

Without a schedule, existing behavior remains; finalists has no default release
and returns 404. DELETE deliberately restores that default. A closed gallery or
winners window returns empty listings and 404 for inaccessible detail/card URLs;
feedback returns 403; unreleased finalists/archives return 404.

Public event responses and feedback use `no-store`; the existing service worker
respects it. Previously downloaded content and issued artifact URLs cannot be
revoked by a later schedule. Schedules are retained by database backup/restore;
canonical archive/template import does not currently carry these extension rows.
Organizer scheduling is API-based; no visual editor is added in this batch.
