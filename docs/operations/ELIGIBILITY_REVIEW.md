# Eligibility review and participant remediation

Organizers define objective rules per event, review each project, and give participants a structured way to fix problems.

**Rules** (`PUT .../eligibility-rules/`): team size min/max, required artifact kinds, finalized submission, track chosen, and `require_clearance` (when on, only _cleared_ projects are judgeable). Everything else is raised by hand.

**Review** (per project, `.../projects/<p>/eligibility/`): status `pending` → `needs_remediation` → `cleared` | `ineligible`, plus findings (`open` → `addressed` by a member → `resolved`/`waived` by an organizer).

| Call                               | Who       | Effect                                                                                                                          |
| ---------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `POST checks/`                     | organizer | Reconcile automated findings with the rules now: open new, auto-resolve met ones. A waived automated finding is never reopened. |
| `POST findings/`                   | organizer | Manual finding (blocking/advisory).                                                                                             |
| `POST findings/<f>/respond/`       | member    | Describe the fix; review returns to `pending` once no blocking finding is still `open`.                                         |
| `POST findings/<f>/close/`         | organizer | `resolved`, or `waived` with a required reason.                                                                                 |
| `POST decision/`                   | organizer | Re-checks first. `cleared` needs every blocking finding closed; `ineligible` needs a reason.                                    |
| `GET eligibility-reviews/?status=` | organizer | Queue with open/addressed counts.                                                                                               |

Members see only their own project's review; other participants, judges and non-members get 404. Project members receive an in-app message when findings are raised or a decision is made. Every change is audited and emitted through the outbox (`eligibility.*`). Archived events are read-only.

**Effect:** `ineligible` removes a project from judging candidates, progress denominators and award selection; existing ballots are never deleted. `pending` reinstates it. Public gallery visibility is unchanged. Reviews are carried in v2 final archives.
