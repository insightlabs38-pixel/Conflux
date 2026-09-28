# Workspace portfolio (PVS14)

Read-only, workspace-wide views over people and projects across events. Nothing is stored; every row is derived from existing records, so it can never disagree with them.

| Route (`/api/v1/workspaces/{ws}/portfolio/…`) | Who | Returns |
|---|---|---|
| `me/` | any workspace member | the caller's own projects across events: event, team, track, per-stage submission status/version/finalized time, and awards **once the award is published** |
| `projects/?event=&status=finalized\|unfinalized&q=&limit=&offset=` | organizer/admin | every project in the workspace, newest event first; `limit` ≤ 100 |
| `participants/?q=&limit=&offset=` | organizer/admin | one row per person with event, project and finalized-project counts and last join time (usernames only) |
| `participants/{user}/` | organizer/admin | that person's projects across events; 404 for anyone without a project in this workspace |

Isolation: every query is filtered by the workspace in the URL, so other workspaces' people and projects never appear; participants get no organizer routes (403). Query count is constant in the number of projects (guarded by a test).
