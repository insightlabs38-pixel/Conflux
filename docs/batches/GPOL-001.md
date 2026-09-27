# GPOL-001 — Organizer workflow consistency
## Result
Complete. Workspace deep links now wait for a verified role, and cloned events open in the dashboard without a reload.
## Changes
- Deny unknown workspace memberships and show a retryable error when the membership request fails.
- Refresh and select events created by clone or template instantiation.
## Verification
- `pnpm --dir src/web exec vitest run features/event-builder/EventTemplatesPanel.test.tsx app/App.navigation.test.tsx` → 9 passed.
- `pnpm --dir src/web lint` → passed.
## Limitations
- No recorded-surface or scene manifest exists yet; footage impact: unaffected.
## Next
GPOL-002: participant teams, forms, artifacts, and submission consistency pass.
