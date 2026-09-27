# GPOL-003 — Judge and public workflow consistency
## Result
Complete. Judges can reach private events and failed ballot draft saves remain visible; public event pages expose the existing gallery.
## Changes
- Added role scoped judge event discovery and reset review context when an event or stage changes.
- Serialized draft saves, retained unsaved status after failure, and stopped ballot submission when saving fails.
- Linked the public gallery and made award loading failures retryable.
## Verification
- Web Vitest → 57 passed; TypeScript lint → passed.
- Participation integration tests → 14 passed; Ruff checks → passed.
- Generated OpenAPI validation and checked artifact → passed.
## Limitations
- No recorded-surface or scene manifest exists yet; footage impact: unaffected.
## Next
GPOL-004: responsive, accessibility, loading, error, and empty state gate.
