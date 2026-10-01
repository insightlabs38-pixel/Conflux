# Event timeline (TIMELINE)

One ordered, derived view of everything time-boxed about an event. Nothing is stored. Code: `core/timeline.py` (contract), `core/timeline_views.py`, providers in `eventconfig/timeline.py`; web `lib/timeline.ts`, `features/operations/TimelinePanel.tsx` (Operations > Timeline) and the "Coming up" card in the organizer overview.

## What is on it

| Kind           | Source                                                                           | Changed through                                   |
| -------------- | -------------------------------------------------------------------------------- | ------------------------------------------------- |
| `event`        | the event's start and end                                                        | `PATCH events/{e}/`                               |
| `gate`         | each temporal gate (registration, submission, ...); one date alone is an instant | `PATCH events/{e}/temporal-gates/{id}/`           |
| `publication`  | each publication schedule                                                        | `PUT events/{e}/publication-schedules/{surface}/` |
| `agenda`       | agenda sessions (including ones not on the public agenda)                        | `PATCH events/{e}/agenda/{id}/`                   |
| `voting`       | the community voting window                                                      | `PATCH events/{e}/voting-plan/`                   |
| `office_hours` | mentor office-hour slots                                                         | no edit endpoint (read-only here)                 |
| `reminder`     | reminders still to be sent (not sent, not cancelled)                             | cancel in Communications                          |

Existing `GET events/{e}/timezone-timeline/` (event window plus gates, with DST notes) is unchanged; the new endpoint is the general one.

## API

`GET /workspaces/{w}/events/{e}/timeline/` (organizer or admin)

| Parameter    | Meaning                                                                                         |
| ------------ | ----------------------------------------------------------------------------------------------- |
| `from`, `to` | ISO 8601 with an offset (`...Z`); items that end at or after `from` and start at or before `to` |
| `kinds`      | comma list of kinds; an unknown kind is a 400                                                   |
| `limit`      | 1-500, default 200; `total` says how many matched                                               |

Answer: `{event, timezone, total, items[], conflicts[]}`. Each item has `kind`, `kind_label`, `key` (`<kind>:<id>`, stable), `label`, `starts_at`/`ends_at` (UTC; `ends_at` null for an instant), `local_starts_at`/`local_ends_at` (the event's zone, with offset), `dst_note` (when the window crosses a daylight-saving change), `source`, `note`, `editable` and `write`. Items are ordered by start, then kind, then key.

**`write`** is the existing endpoint that changes the item's times: `{method, path, fields, extra}`. `path` has `{workspace}` and `{event}` placeholders (relative to `/api/v1/`), `fields` maps `starts_at`/`ends_at` to the body field each is sent as, `extra` are constant fields the endpoint needs next to the times (a finalists schedule's stage). A change is therefore the domain's own request, with its own validation, audit and versioning; the timeline never writes.

## Conflicts

Advisory facts, never blocks, deterministic (no clock, no heuristics). They are judged on the whole event and then shown when they touch an item in the answer.

- `window_inverted`: an item ends at or before it starts.
- `<axis>_overlap` (`location`, `track`, `mentor`): two items on the same exclusive resource overlap. Windows that only touch do not.
- `outside_event`: an agenda session or office-hour slot lies outside the event's dates (only when the event has both dates).
- `publication_before_voting_closes`: finalists, winners or feedback publication opens while community voting is still open.

## Adding to it

```python
from core import timeline
timeline.register_provider(timeline.Provider("my_kind", "My things", lambda event: [
    timeline.TimelineItem("my_kind", f"my_kind:{row.public_id}", row.title, row.starts_at, row.ends_at,
                          group={"desk": str(row.desk_id)}, editable=True,
                          write=timeline.Write("PATCH", "workspaces/{workspace}/events/{event}/things/" + str(row.public_id) + "/",
                                               {"starts_at": "starts_at", "ends_at": "ends_at"}))
    for row in event.things.all()[:1000]]))
timeline.register_rule(my_rule)   # my_rule(event, items) -> [timeline.Conflict(code, message, (keys...))]
```

A provider only reads, caps its rows, and names an existing endpoint or none.

## Web

Times are shown on the event's own clock, grouped by day, with the zone stated. "Change times" opens the item's two fields in the event's wall time; the web converts them to UTC (`zonedToUtc`: a time skipped by a clock change lands just after the gap, a repeated one is read as the first) and sends them to the item's `write`. The domain's refusal is shown as is. The overview's "Coming up" card lists the next five items and counts conflicts among them.

## Compatibility and limits

Additive and stateless: no table, no migration, one new endpoint. Not built: participant-facing or public timelines, a calendar grid view, drag to reschedule, editing office hours and reminders, stage-level times (stages carry none), and the judging window (judging has no dates; community voting stands in for the "publication before judging ends" rule).
