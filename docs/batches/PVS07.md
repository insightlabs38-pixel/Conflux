# PVS07 — Audit capsule + decision explanation
## Result
Organizers can export a signed, pseudonymous capsule verifiable offline, and produce deterministic explanations of a project's rank for organizers and (aggregated) participants.
## Changes
- `evaluations.capsule`, `evaluations.explain`, `scripts/verify_capsule.py`; endpoints `audit-capsule/` and `explain/<project>/`.
## Verification
- `test_audit_capsule.py` → 9 passed, including the standalone script accepting an honest capsule and rejecting five forgeries (edited score, re-checksummed edit, reordered results, wrong key, no key).
## Limitations
- Rubric plans only; the verifier tolerates 1e-6 because pseudonymous labels change solver ordering.
- Footage unaffected: no public surface changes.
## Next
PVS08.
