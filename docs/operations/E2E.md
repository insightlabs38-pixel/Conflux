# Browser journeys, screenshots and clips

`tests/e2e` holds Playwright specs that run against a live, demo-seeded stack (see docs/operations/DEMO.md once PVS-H05 lands; for now `manage.py demo_scenario create --seed 7 --participants 24 --judges 6 --password demo-pass-7 --public`).

```sh
E2E_BASE_URL=http://localhost:8080 npx playwright test -c tests/e2e/playwright.config.ts
# one scene set only (desktop, video on): ... scenes
```

Env: `E2E_BASE_URL`, `E2E_DEMO_SEED` (7), `E2E_DEMO_PASSWORD` (demo-pass-7). Chromium must be installed (`npx playwright install chromium`).

- `signin`, `public`, `roles`: sign-in/out, public pages, organizer/judge/participant workspaces at 1280×800 and 390×844 — no console errors or failed requests, no horizontal overflow, axe WCAG 2 A/AA clean, skip-link and focus-ring keyboard checks. Loading states must resolve before assertions.
- `scenes` (desktop): deterministic screenshots in `tests/e2e/artifacts/scenes/` and one video per scene under `artifacts/results/*/video.webm`. Failures keep traces (`npx playwright show-trace`).
