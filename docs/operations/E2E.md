# Browser journeys, screenshots and clips

`tests/e2e` holds Playwright specs that run against a live, demo-seeded stack (`scripts/demo-reset`, see [DEMO.md](DEMO.md)).

```sh
E2E_BASE_URL=http://localhost:8080 npx playwright test -c tests/e2e/playwright.config.ts
# one scene set only (desktop, video on): ... scenes
```

Env: `E2E_BASE_URL`, `E2E_DEMO_SEED` (7), `E2E_DEMO_PASSWORD` (demo-pass-7). Chromium must be installed (`npx playwright install chromium`).

- `signin`, `public`, `roles`: sign-in/out, public pages, organizer/judge/participant workspaces at 1280×800 and 390×844 — no console errors or failed requests, no horizontal overflow, axe WCAG 2 A/AA clean, skip-link and focus-ring keyboard checks. Loading states must resolve before assertions.
- `scenes` (desktop): deterministic screenshots in `tests/e2e/artifacts/scenes/` and one video per scene under `artifacts/results/*/video.webm`. Failures keep traces (`npx playwright show-trace`).
- `lifecycle` (desktop, serial): the recorded demo lifecycle through the UI only — participant creates team and project, submits and receives a signed receipt; organizer requests changes, participant remediates, organizer clears; three judges inspect artifacts and score; organizer publishes results, finalizes in the deliberation room, publishes the award; the public results page shows it. Needs a fresh `scripts/demo-reset submitted` (it consumes participant-24).
- `pvs`: mentor desk, volunteer check-in by pass, participant RSVP/office hours/mentor request, deadline-exception request and decision, rules publish and acknowledge, and a layout/axe check of every organizer operations panel (also at 390×844). Workflows run on desktop only; run after a reset.
- Addressing: people by username, the event through the API; the event's public ID is also stable across resets.
