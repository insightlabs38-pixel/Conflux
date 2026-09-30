# Escalation Protocol

Escalation is for genuine ambiguity/risk, not a substitute for debugging.

## Categories

- `architecture` — canonical representation/service boundary/primitive conflict
- `product` — product behavior materially underspecified
- `design` — approved design conflicts with real workflow/data/accessibility
- `security` — authz, secrets, injection, unsafe content, isolation
- `data_integrity` — possible corruption, race, irreversible official state
- `migration` — safe upgrade/compatibility path unclear
- `performance` — required SLO/capacity cannot be reached without architecture change
- `test_infra` — verification cannot produce trustworthy evidence
- `ownership_collision` — parallel work cannot proceed safely
- `plan_defect` — task/dependency/spec itself is wrong or self-contradictory
- `external_dependency` — required external provider/tool behavior blocks progress

## Severity

- **P0:** active security/data-loss/integrity incident; stop affected mutation immediately.
- **P1:** correctness/architecture blocker or issue that can invalidate official results/migrations/security.
- **P2:** localized product/design ambiguity or significant noncritical blocker.
- **P3:** improvement/cleanup question that does not block safe progress.

## Worker behavior

Before escalating:
1. inspect the relevant task/spec/code/tests;
2. use targeted `rg`, `grep`, `sed`, exact file reads and Git history as appropriate;
3. attempt bounded local diagnosis;
4. identify the smallest decision actually needed.

Do not spend unbounded time guessing around an architecture ambiguity explicitly listed in `escalate_if`.

Write:
`docs/execution-v3/escalations/<ESC-ID>.yaml`

Then return the task as `blocked`/`corrections` as appropriate.

## Controller behavior

P0/P1:
- freeze affected lock groups;
- do not promote dependent tasks;
- route to the required frontier/human reviewer;
- record resolution in the escalation file;
- amend spec/task if the plan itself changed.

P2:
- may continue unrelated work;
- resolve before the affected task closes.

P3:
- may be queued as follow-up if it does not violate current acceptance.

## Resolution

A resolution must say:
- decision;
- rationale;
- changed contracts/tasks, if any;
- migration/backfill, if any;
- verification needed.

Do not resolve by editing the code while leaving the controlling spec contradictory.
