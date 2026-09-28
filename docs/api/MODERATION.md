# Unified moderation review

Organizers and administrators use the event-scoped API:

- GET `operations/moderation/` for five review sections.
- POST `operations/moderation/reviews/` to record a decision.
- GET `operations/moderation/reviews/` for immutable review history.

These paths follow `/api/v1/workspaces/{workspace}/events/{event}/` and are
available through the generated SDKs and API explorer. Queue and history
support `kind` and `offset`; each queue section/history page contains at most
50 records. Queue counts reflect live source records, including evidence that
has already been acknowledged. `review_current` indicates whether the latest
review still matches the current evidence. Offset pagination reflects live
state; refresh after decisions that remove items.

| Kind          | Evidence                                                                                                                             | Available decisions                 |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
| `duplicate`   | Matching declared SHA256 across distinct event projects, with counts and up to 50 artifact samples. This is an indicator for review. | dismiss, escalate                   |
| `voting`      | Unresolved abuse signals and their existing evidence; raw voter tokens are excluded.                                                 | resolve, escalate                   |
| `content`     | Visible project comments. Inclusion requests review and does not imply abuse.                                                        | hide, dismiss, escalate             |
| `artifact`    | Rejected artifacts or non-OK latest checks per validator; at most 50 checks displayed.                                               | acknowledge, escalate               |
| `eligibility` | Pending/waitlisted event applications, notes and status.                                                                             | approve, reject, waitlist, escalate |

Copy `kind`, `source_key` and `evidence_digest` from a queue item; submit these
with `disposition` and a nonblank `note` (at most 2,000 characters). A changed or
unavailable source returns HTTP 409 and requires refreshing the queue.
Inapplicable actions and malformed inputs return HTTP 400. Archived events
permit reading and reject decisions.

Reviews preserve the inspected evidence, actor, note and disposition. Source
actions, review snapshots and audit records commit atomically. PostgreSQL
locks serialize competing decisions. Resolved signals/hidden comments/decided
applications leave their active section; their review history remains.

Duplicate dismissal does not merge/delete projects. Artifact acknowledgement
does not change status, bypass validation or make submission eligible.
Application decisions reuse existing organizer registration semantics.
Escalation records a disposition for follow-up without messaging anyone.
There is no new visual editor or automatic content classifier.
