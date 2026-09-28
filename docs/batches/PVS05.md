# PVS05 — Declarative Event-as-Code
## Result
Event configuration can be exported as portable YAML/JSON, validated, planned as a rolled-back trial apply, and applied atomically with stale-plan protection.
## Changes
- `integrations.eventascode` (name-keyed sections, dependency-ordered sync, immutability guards) with API and `eventascode` command; adds `pyyaml` as a runtime dependency.
## Verification
- `test_event_as_code.py` → 18 passed (fixed-point export, plan==apply, idempotence, stale digest, precise validation errors, immutable evidence, opt-in prune, rebuild into an empty event, authz, YAML command).
## Limitations
- Form versions, registration settings, webhooks and pool membership are not covered; omitted optional fields are unchanged rather than reset.
- Footage unaffected: no public surface changes.
## Next
PVS-H01.
