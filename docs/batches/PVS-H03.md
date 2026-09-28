# PVS-H03 — Frontend, accessibility and browser-journey hardening
## Result
Inspecting the real rendered stack found that the web app was never served by Compose and had no sign-in; both are fixed, public pages are styled, and a deterministic Playwright suite (32 tests, desktop + mobile, axe) with scene screenshots and clips now passes.
## Changes
- Image builds and bundles the React app (served at `/app/`, `/` redirects with query); sign-in form with optional SSO button and a sign-out control.
- Public server-rendered pages (were serif/default-blue) get typography/link/control styling from existing tokens; forms across the app get visible control borders and label spacing. No redesign.
- Community voting no longer requests results for events without voting (a 404 on every public event view).
- `tests/e2e` suite + `docs/operations/E2E.md`; Playwright/axe added as dev dependencies.
## Verification
- Playwright against a fresh Compose build: 32 passed (sign-in, public pages, three role workspaces, keyboard, axe, overflow, console/network clean).
- Web unit tests 125 passed; tsc, prettier and ruff clean; Python suite 1289 passed.
## Limitations
- PVS01–PVS15 capabilities have no dedicated UI panels (reachable via API/API explorer/MCP); the demo event has a sparse landing page.
- Footage: baseline recaptured from this build; earlier screenshots are superseded.
## Next
PVS16, PVS17 (if before the 08:00 UTC feature cut), then PVS-H04.
