# PVS11 — Governance utility pack
## Result
New `governance` app adds versioned rules with acknowledgements, opt-in two-organizer result-publication approval, visible correction history, immutable signed submission receipts, judge assignment accept/decline and participant deadline-exception requests that feed the existing `ExceptionGrant`.
## Changes
- Approval, direct publish and corrections share one write path (`governance.services.apply_publication`); default behaviour is unchanged unless an event opts in.
- A decline reuses `ConflictOfInterest`, so exclusion and ballot rejection are the existing enforced semantics; approvals create ordinary `ExceptionGrant`s (≤ 7 days).
- Receipts are issued in the finalize transaction and verify through the existing record-verification endpoint.
- Fixed latent bug: `check_action` used the first matching grant, so an expired older grant hid a newer active one.
- Rules versions, acknowledgements, corrections and receipts are in the final archive; requests/responses are operational and excluded like grants.
## Verification
- `test_governance.py` (12) + PostgreSQL `test_governance_races.py` (3: duplicate requests, double approval, concurrent acks/publications) → 15 passed.
- Full SQLite suite, security route sweep (now substitutes ints for `<int:>`), archive guard, `spectacular --fail-on-warn`, SDK + OpenAPI checks → clean.
## Limitations
- No UI (PVS-H03); acknowledgements gate nothing; only the `submit` action is exception-requestable; a single-organizer workspace cannot use publication approval.
## Next
PVS12 (optional generic OIDC/SSO).
