# PVS01 — Eligibility review + participant remediation
## Result
Organizers can rule on project eligibility with explicit findings, and participants can see and answer them; rulings change who can be judged or awarded.
## Changes
- New `eligibility` app: rules, reviews, findings, audited state machine with in-app notification and outbox events.
- Ineligible (or, when required, uncleared) projects leave `eligible_projects` and `select_winner`; reviews travel in v2 final archives and are covered by per-subject privacy export.
## Verification
- `test_eligibility_review.py` → 8 passed (authz/isolation, remediation loop, waiver stickiness, clearing rules, judging/award effect, archived freeze); final-archive round trip extended.
## Limitations
- No participant UI yet (API only, PVS-H03 for selected flows); gallery visibility unaffected by rulings.
- Footage unaffected: no public surface changes.
## Next
PVS02.
