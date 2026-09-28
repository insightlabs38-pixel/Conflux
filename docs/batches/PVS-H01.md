# PVS-H01 — Security/integrity/concurrency hardening
## Result
Seven defects fixed (two P1); standing route, isolation, fuzz and PostgreSQL race suites now guard the whole API surface. Details: `docs/verification/PVS-H01/findings.md`.
## Changes
- Rate-limit client identity behind the proxy; scoped/in-flight-safe idempotency; cross-origin write refusal; login throttle; cookie flags; object-only JSON; voting-candidate gating.
## Verification
- Full suite on SQLite → 1153 passed, 20 skipped; on PostgreSQL 17 → 1168 passed, 5 skipped; OpenAPI/SDK regenerated.
## Limitations
- Unhashed session tokens at rest; account lockout is per username.
## Next
PVS06.
