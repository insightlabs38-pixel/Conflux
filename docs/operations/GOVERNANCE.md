# Governance utilities (PVS11)

All routes sit under `/api/v1/workspaces/{ws}/events/{event}/` unless noted.

| Capability | Routes | Semantics |
|---|---|---|
| Participant rules | `rules/`, `rules/{n}/`, `rules/acknowledge/`, `rules/acknowledgements/` | Organizer publishes immutable numbered versions; members acknowledge only the current version (a new version resets acknowledgement); organizers see who has and has not acknowledged. Informational: no action is blocked on it. |
| Publication approval | `governance/settings/` (`require_publication_approval`), `result-publication-requests/` (+ `{id}/approve|reject|cancel/`) | Opt-in per event. When on, `publish-results/` is refused and a request needs a *different* organizer's approval; approval runs the same write path as direct publication. |
| Correction history | `result-corrections/`, public `/api/v1/events/{event}/result-corrections/` | Replacing an already-published run or tie-break set records an immutable correction (previous/new run number, reason, time; never scores). Participants and the public see it only once the plan's results are visible to participants. Direct `publish-results/` accepts an optional `reason`; approval requests require one when replacing results. |
| Submission receipt | `projects/{p}/submissions/{stage}/receipt/[?version=n]` | A signed `submission_receipt` record (digest, version, timestamp) issued inside the finalize transaction, stored immutably, verifiable at `/api/v1/records/verify/`. Versions finalized before PVS11 get theirs on first request. |
| Assignment response | `stages/{s}/evaluation-plans/{plan}/my-assignments/`, `…/{project}/respond/`, `…/assignment-responses/` | Judges accept or decline (reason required). A decline creates the existing conflict-of-interest recusal, so it is excluded from the next assignment and ballots are rejected. Declines are final for the judge and impossible after a ballot exists; organizers see counts and reasons and use the existing rebalance. |
| Deadline exception | `projects/{p}/exception-requests/`, `exception-requests/` (+ `{id}/approve|reject|cancel/`) | Project members request; an organizer approves with an expiry ≤ 7 days, which creates a normal `ExceptionGrant` (action `submit`, subject = the project). As before, a grant overrides policy gates only, never the hard event deadline. |

Grant matching now considers only active grants, newest first, so a fresh exception is honoured even when an older grant for the same project has expired.
