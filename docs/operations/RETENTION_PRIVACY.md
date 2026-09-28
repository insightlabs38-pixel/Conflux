# Retention and privacy controls

Organizer-only, per event, all under `/api/v1/workspaces/<w>/events/<e>/privacy/`.

| Endpoint                                | Purpose                                                                                       |
| --------------------------------------- | --------------------------------------------------------------------------------------------- |
| `GET/PUT retention-policy/`             | `participant_data_days`, `private_artifact_days` (null = never), counted from `event.ends_at` |
| `POST retention/run/` `{apply}`         | Preview (default) or apply whichever windows are due                                          |
| `POST subjects/<user>/export/`          | Export one person's event data; audited                                                       |
| `POST subjects/<user>/erase/` `{apply}` | Preview (default) or erase that person's event data                                           |

`python src/api/manage.py enforce_retention [--apply]` runs the same enforcement for every event with a policy (previews by default; schedule it externally).

## Erased

Applications, marketplace profiles, saved searches, check-ins, message receipts and comments, plus non-public stored artifacts (participant/judge/organizer visibility). Public artifacts are never purged.

## Retained (reported, never rewritten)

Team/project memberships, submissions and frozen versions, form responses, ballots, assignments, pairwise comparisons, appeals, awards and audit history — results must stay verifiable. Artifact rows keep title, kind, size and `sha256`; status becomes `purged`.

## Safety

- Artifacts of projects with a pending appeal are held and reported until it is decided.
- Purge is two-phase: the row is marked `purged` in the audited transaction, then the object is deleted and its key cleared. A storage failure leaves the key, so the next run retries; a purged artifact can never become `ready` again.
- Audit entries record counts only, never personal content.
- Not carried in v2 final archives (operational). Erasure does not delete the account itself, which is workspace-wide.
