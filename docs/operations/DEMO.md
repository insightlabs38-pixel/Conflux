# Final demo runbook

## Prepare (2 minutes, repeatable)

```sh
make up                       # or `docker compose up -d --build --wait`
make demo-reset               # purge + recreate the deterministic demo event, prints URLs/logins
```

`scripts/demo-reset` only ever purges the generated `demo-hackathon-<seed>` workspace. It builds a synthetic hackathon (seed 7: 24 teams, 6 judges, blind rubric judging, normalization, published results, awards) through the real API, then `demo_showcase` adds a full landing page, agenda, expo tables, participant rules with acknowledgements and two post-event continuations. Same seed → same content (public IDs are fresh UUIDs each run, so use the printed URLs). Shared password: `demo-pass-7`.

Accounts: `demo-hackathon-7-organizer`, `-judge-01…06`, `-participant-01…24`.

## Script (~7 minutes)

1. **Public site** — `/e/<event>/`: landing, tracks, gallery, published awards. Open the gallery and one project page; open `/results/` and an award story (shareable card).
2. **Agenda & expo** — `/agenda/` (add the `.ics` feed to a calendar), `/map/` (print preview), `/badge.svg`, `/api/v1/events/<event>/state/`.
3. **Organizer** — sign in at `/app/`: operator console, launch readiness, audit trail, templates/clone. Point out judging results, publication history and API explorer (`/app/?api=explorer`).
4. **Judge** — sign in as `judge-01`: invitations/expertise, assigned queue, blind ballots. Explain peer-score isolation (a judge cannot read another judge's ballots).
5. **Participant** — sign in as `participant-01`: team/project workspace; show the portfolio, rules, and receipt endpoints in the API explorer.
6. **Differentiators (API/MCP)** — eligibility review, deliberation room, judging replay and the signed audit capsule, publication approval + correction history, maintenance mode (503 with message), MCP adapter (`docs/operations/MCP.md`) with a scoped credential.
7. **Ops** — `make backup`, `make backup-restore-smoke`, offline boot (`make cold-boot-smoke`).

## Assets

`make demo-e2e` (needs the stack above) regenerates, in `tests/e2e/artifacts/`: `scenes/*.png` (landing, gallery, results, agenda, expo map, organizer/judge/participant workspaces, API explorer, sign-in) and one `video.webm` per scene under `results/`. Failures keep traces. The same run is the pre-recording smoke test: 37 checks incl. accessibility, overflow and console/network errors.

## Recovery

- Anything odd on stage: `make demo-reset` (≈20 s) and sign in again.
- Stack unhealthy: `docker compose ps`, `docker compose logs app`; `docker compose restart`.
- Nothing needs the internet; if the network drops the demo is unaffected. Optional SSO is off unless configured.

## Known limits to avoid on stage

PVS features (eligibility, deliberation, replay/capsule, governance, portfolio, continuation, agenda editing, MCP) are API-driven; use the API explorer or curl rather than looking for screens. The event is _closed_ with results published, so live submission is shown through the participant workspace and API rather than a running clock.
