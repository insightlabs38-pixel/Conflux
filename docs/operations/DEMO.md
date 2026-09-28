# Final demo runbook

## Prepare (2 minutes, repeatable)

```sh
make up                       # or `docker compose up -d --build --wait`
make demo-reset               # purge + recreate the demo at the `submitted` checkpoint, prints URLs/logins
scripts/demo-reset judged     # other checkpoints: submitted (default) | judged | published
```

`scripts/demo-reset` only ever purges the generated `demo-hackathon-<seed>` workspace and rebuilds it through the real API. Same seed → same content **and the same event/workspace public IDs** (they are derived from the seed, so the printed URLs and the runbook links below survive every reset). Shared password: `demo-pass-7`.

Checkpoints (each includes the previous):

| Checkpoint            | State                                                                                                                                                                                                                                                                                                                       |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `submitted` (default) | Event **open**; 22 of 24 teams have finalized submissions; `participant-23` and `-24` are approved but have no team (they create → submit on camera); 6 judges, no ballots; results unpublished; agenda, expo tables, rules, sponsor resources, a mentor, a volunteer, one eligibility finding, RSVPs and check-ins seeded. |
| `judged`              | Every judge has scored every submitted project; results still unpublished.                                                                                                                                                                                                                                                  |
| `published`           | Closed archive: results normalized and published, awards decided, continuation listings (the previous default).                                                                                                                                                                                                             |

Accounts: `demo-hackathon-7-organizer`, `-judge-01…06`, `-participant-01…24`, `-mentor`, `-volunteer`, `-sponsor`. Tests and scripts address people by username and the event by discovering it through the API (or the fixed ID); nothing depends on random IDs.

Accounts: `demo-hackathon-7-organizer`, `-judge-01…06`, `-participant-01…24`.

## Script (~7 minutes)

1. **Public site** — `/e/<event>/`: landing, tracks, gallery, published awards. Open the gallery and one project page; open `/results/` and an award story (shareable card).
2. **Agenda & expo** — `/agenda/` (add the `.ics` feed to a calendar), `/map/` (print preview), `/badge.svg`, `/api/v1/events/<event>/state/`.
3. **Organizer** — sign in at `/app/`: operator console, launch readiness, audit trail, templates/clone. Point out judging results, publication history and API explorer (`/app/?api=explorer`).
4. **Judge** — sign in as `judge-01`: invitations/expertise, assigned queue, blind ballots. Explain peer-score isolation (a judge cannot read another judge's ballots).
5. **Participant** — sign in as `participant-01`: team/project workspace; show the portfolio, rules, and receipt endpoints in the API explorer.
6. **Differentiators** — all in the workspaces now: eligibility review (organizer queue ↔ participant findings), deliberation room with finalist comparison, judge route and artifact inspector, rules acknowledgement, publication approval and correction history, mentor desk, check-in desk; then judging replay and the signed audit capsule and the MCP adapter (`docs/operations/MCP.md`) via the API explorer.
7. **Ops** — `make backup`, `make backup-restore-smoke`, offline boot (`make cold-boot-smoke`).

## Assets

`make demo-e2e` (needs the stack above) regenerates, in `tests/e2e/artifacts/`: `scenes/*.png` (landing, gallery, results, agenda, expo map, organizer/judge/participant workspaces, API explorer, sign-in) and one `video.webm` per scene under `results/`. Failures keep traces. The same run is the pre-recording smoke test: 37 checks incl. accessibility, overflow and console/network errors.

## Recovery

- Anything odd on stage: `make demo-reset` (≈20 s) and sign in again.
- Stack unhealthy: `docker compose ps`, `docker compose logs app`; `docker compose restart`.
- Nothing needs the internet; if the network drops the demo is unaffected. Optional SSO is off unless configured.

## Known limits to avoid on stage

Judging replay, the audit capsule, Event-as-Code, backup/restore, webhooks/MCP and maintenance mode remain CLI/API-first; use the API explorer or the scripts. Judges join deliberation (stances/notes) through the API only; the organizer sees the room and finalizes in the UI. Continuation opens once an event is closed, so show it from the `published` checkpoint.

## Recording the live lifecycle

`scripts/demo-reset submitted`, then follow `tests/e2e/lifecycle.spec.ts` as the script: participant-24 creates a team and project, submits and gets a signed receipt; organizer requests changes, participant remediates, organizer clears; judges 01–03 inspect and score; organizer publishes results, finalizes the Grand Prize in the deliberation room and publishes the award; the public results page shows it. `make demo-e2e` replays the whole thing headlessly (re-run the reset before repeating it).
