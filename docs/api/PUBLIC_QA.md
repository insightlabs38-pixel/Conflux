# Public Q&A and announcements

Public readers use `GET /api/v1/events/{event}/questions/` and
`GET /api/v1/events/{event}/announcements/`. Only public, opened events
(including their closed/archived history) are readable. Lists return at most
50 items with a nonnegative `offset`. Question/answer and announcement text is
plain text; clients must escape it. Author identities are omitted.

Workspace members with participant, judge, organizer or admin roles submit
`{"question":"When is lunch?"}` to
`POST /api/v1/workspaces/{workspace}/events/{event}/communications/questions/`.
The event must be open and public. New questions are pending and never appear
in public responses. GET on this path returns the caller's questions;
organizers/admins see all event questions. There is no anonymous submission.

Organizers/admins review a question at the same path plus `{question}/review/`:
`{"version":1,"status":"published","answer":"Noon.","note":"Checked schedule"}`.
Statuses are `pending`, `published` and `hidden`. Publishing requires a nonblank
answer. Omitting `answer` preserves it; setting an empty answer is allowed only
when the question is not published. Review increments the version and records
the actor, note, and before/after evidence atomically. Stale versions return 409;
refresh before making another decision. Archived events reject reviews.

Existing organizer announcement creation remains immediately published. Review
at `communications/announcements/{announcement}/review/` accepts `version`,
`status` (`published` or `hidden`) and `note`. Hiding retains the source and audit
history, removing it from the public API and existing announcement page block.
Republishing restores it. Existing creation/deletion routes remain available.

These APIs are also available through the generated SDKs and API explorer.
There is no new Q&A page editor, notification delivery, anonymous identity,
threaded discussion, or addition to the separate VS36 cross-domain queue.
