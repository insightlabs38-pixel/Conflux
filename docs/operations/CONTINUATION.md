# Post-event continuation (PVS15)

After an event closes, a member of a project with a finalized submission can publish where the project went next. It is intentionally small: one profile per project plus a bounded update log — no comments, messaging, contact details or fundraising.

| Route | Who | Notes |
|---|---|---|
| `PUT …/projects/{p}/continuation/` | project member | `summary` (≤ 1000), optional `url` (http/https, no embedded credentials), `seeking` ⊆ `contributors, mentors, users, feedback, partners`, `is_public` (default false). Only while the event is `closed`/`archived`. |
| `GET …/projects/{p}/continuation/` | member or organizer | private view including `is_public` and moderation state; other teams get 404. |
| `POST …/projects/{p}/continuation/updates/` | project member | append-only, ≤ 1000 chars, at most 20 per project. |
| `POST …/projects/{p}/continuation/hide/` / `restore/` | organizer | hide requires a reason; a hidden profile stays hidden across member edits until restored. |
| `GET …/continuations/` | organizer | every continuation for the event. |
| `GET /api/v1/events/{event}/continuations/` | public | public, unhidden profiles of public events with the latest 3 updates each; no moderation fields. |

All writes are audited. Continuation rows are part of the final archive. Text is stored and returned as plain text — clients must escape it when rendering.
