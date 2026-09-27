# Reusable judge directory

Organizers can list workspace judges at `GET /api/v1/workspaces/{workspace}/judge-directory/`.
Only existing workspace `judge` memberships appear. The directory does not create accounts or
grant roles.

To invite a judge, create an evaluation pool for the event, then `POST` its public ID and the
judge's public ID to `/api/v1/workspaces/{workspace}/events/{event}/judge-invitations/`.
The judge reads invitations at `GET /api/v1/workspaces/{workspace}/my-judge-invitations/`
and responds with `{"decision":"accept"}` or `{"decision":"decline"}` at
`POST .../my-judge-invitations/{invitation}/respond/`. Acceptance adds the judge to that
event's selected pool; a pending invitation grants no pool access. An organizer can revoke a
pending invitation with `DELETE .../events/{event}/judge-invitations/{invitation}/`.
Declined or revoked invitations can be sent again. Responses are one-time transitions.

The workspace judge role remains required. The existing direct pool-membership API remains
available for organizer-managed rosters; it does not require invitation acceptance. A plan
bound to a pool only admits its pool judges to candidate queues and ballot submission.
Plans without a pool retain their existing workspace-wide judge eligibility.
