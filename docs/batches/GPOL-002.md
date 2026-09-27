# GPOL-002 — Participant workflow consistency
## Result
Complete. Participants can answer published project forms, and workspace navigation clears stale event and invite context.
## Changes
- Added a project scoped form list that exposes latest published versions and participant visible fields only.
- Added typed answer controls with conditional visibility, artifact choices, saved answer loading, and error feedback.
- Clarified unavailable event links and cleared event context when returning to workspaces.
## Verification
- Web Vitest → 54 passed; TypeScript lint → passed.
- Form response integration tests → 12 passed; Ruff checks → passed.
- Generated OpenAPI validation and checked artifact → passed.
## Limitations
- No recorded-surface or scene manifest exists yet; footage impact: unaffected.
## Next
GPOL-003: judge, gallery, and results consistency pass.
