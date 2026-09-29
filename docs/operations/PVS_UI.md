# PVS features in the product UI

The human workflows live in the existing role workspaces (`/app/`); there is no separate PVS dashboard. Each panel calls the same API as everything else, so it can never do more than the API allows for that role.

| Feature                  | Who         | Where                                                                                                                                                                                                              |
| ------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| PVS01 eligibility        | Organizer   | Event dashboard → **Eligibility review**: queue, run checks, add findings, resolve/waive, approve / request changes / reject                                                                                       |
|                          | Participant | Project → **Eligibility review**: structured findings, describe the fix and resubmit                                                                                                                               |
| PVS02 deliberation       | Organizer   | Event dashboard → **Deliberation and finalization**: finalist table (raw vs normalized score, judge disagreement, close calls, coverage), panel tally, open/close room, finalize winners (override needs a reason) |
| PVS03 hybrid/on-site     | Organizer   | **On-site operations**: RSVP counts, pass scan or manual check-in, rooms/tables, placements, auto-assign preview/apply                                                                                             |
|                          | Volunteer   | Volunteer workspace → event desk: scan or paste a pass (no layout controls)                                                                                                                                        |
|                          | Participant | **Attending**: RSVP and the QR check-in pass                                                                                                                                                                       |
| PVS04 physical route     | Judge       | Judging → **Your judging route** (remaining stops, walking order, unplaced projects)                                                                                                                               |
|                          | Organizer   | **Judging logistics**: per-judge route feasibility and assignment responses                                                                                                                                        |
| PVS08 artifact inspector | Judge       | Review queue → selected project → **Submitted artifacts**: verdict, findings, facts, inert text preview, run/re-run inspection                                                                                     |
| PVS09 sponsor resources  | Participant | **Sponsor challenges and resources** on the event page                                                                                                                                                             |
| PVS10 mentorship         | Participant | Project → **Mentorship**: request a mentor, book/cancel office hours                                                                                                                                               |
|                          | Mentor      | Mentor workspace → **Mentor desk**: availability, claim/resolve queue, schedule office hours                                                                                                                       |
|                          | Organizer   | **Mentor desk** with reassignment                                                                                                                                                                                  |
| PVS11 governance         | Participant | **Event rules** (acknowledge), project **Deadline exception** request, signed **submission receipt** in the Submission panel                                                                                       |
|                          | Judge       | **Your assignments** accept/decline                                                                                                                                                                                |
|                          | Organizer   | **Event rules** (publish, who has acknowledged), **Publication approval and corrections**, **Deadline exception requests**                                                                                         |
| PVS14 portfolio          | Participant | **Profile & history** → **My portfolio**                                                                                                                                                                           |
| PVS15 continuation       | Participant | Project → **After the event** (opens once the event is closed)                                                                                                                                                     |
|                          | Organizer   | **Post-event continuation**: hide/restore listings                                                                                                                                                                 |

## UI-v2 navigation (B02)

Use the persistent desktop sidebar or the mobile **Navigation** disclosure.
Event/stage selectors stay in the workspace context; destination changes retain
form drafts and the judge's offline buffers. Direct links use `view` in the URL.

| Role             | Destination                       | Existing workflows                                                                                          |
| ---------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Participant      | Team                              | Roster, invitations, marketplace                                                                            |
| Participant      | Project & submission              | Project, artifacts, preflight, forms, submission/receipt, eligibility, exceptions, mentorship, continuation |
| Participant      | Event resources                   | Rules, sponsor challenges/resources, RSVP and sessions                                                      |
| Participant      | Profile & history / Messages      | Portfolio / inbox                                                                                           |
| Judge            | Review queue                      | Assignments, project scoring, artifact inspector                                                            |
| Judge            | Schedule & route                  | Calendar and remaining route                                                                                |
| Judge            | Judge profile / Messages          | Invitations and expertise / inbox                                                                           |
| Organizer        | Event setup                       | Settings, tracks/prizes, stage/policy/form/page builders, rules and templates                               |
| Organizer        | Participants & teams              | Registration, teams, mentor desk                                                                            |
| Organizer        | Projects & eligibility            | Review queue, findings, decisions, exception requests                                                       |
| Organizer        | Judging                           | Evaluation plans, rubric, workload, logistics, community voting                                             |
| Organizer        | Results & publication             | Awards, deliberation, approvals/corrections                                                                 |
| Organizer        | On-site / Communications          | Check-in/layout / messages                                                                                  |
| Organizer        | Integrations / Operations & audit | Webhooks / console, health, continuation moderation, config history, permissions                            |
| Mentor/volunteer | Mentor desk / Check-in desk       | Existing staff workflows; Messages is separate                                                              |

The account disclosure provides sign-out; participants/judges can open profile
history from it. Reusable identity is added in B04; a portfolio remains history.

## Intentionally API/CLI-first

PVS05/06/07/12/13 are technical/operator features (for example judging replay and the audit capsule, SSO configuration and the MCP adapter) better served by the CLI, scripts and API explorer. Also API-only by design: judges' deliberation stances and notes (there is no judge-facing way to discover an award's room, and peer ballots are never shown), mentor reassignment targets beyond available mentors, sponsor portal writes, and eligibility rule configuration.

A panel that fails to render (for example an unexpected server payload) degrades to a retryable notice rather than blanking the workspace.
