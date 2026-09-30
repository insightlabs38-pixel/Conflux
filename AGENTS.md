# AGENTS.md — Conflux Product Depth v3

This repository uses the Product Depth v3 execution system.

## Before doing work

For an assigned task:

```bash
python scripts/pdv3/task_context.py "$TASK_ID"
git status --short
git branch --show-current
```

Read only the task's referenced spec/design/current code.

Use targeted inspection (`rg`, `grep`, `sed -n`, `head`, `tail`, narrow `find`, exact files). Use targeted `rg`/`grep`/`sed` reads and edits on the large queue files as needed; avoid dumping irrelevant large ranges or generated trees into context.

## Authority

Read and follow:
- `docs/product-depth-v3/EXECUTION_PRINCIPLES.md`
- `docs/execution-v3/COMPLETION_RULES.md`
- `docs/execution-v3/LOCKING_AND_PARALLELISM.md`
- `docs/execution-v3/ESCALATION_PROTOCOL.md`
- `prompts/STANDARD_IMPLEMENTATION_PROMPT.md`

Task-specific fields/specs/design refs override generic convenience.

## Non-negotiable rules

- Implement the full task/depth contract, not a checkbox version.
- Reuse canonical primitives; do not introduce parallel truth models.
- Preserve server-side authorization, validation, audit, versioning and lifecycle invariants.
- Do not weaken tests/gates, fake evidence, or hide regressions behind skips/timeouts.
- Do not use destructive Git operations on unowned work.
- Stay inside assigned ownership/locks unless a small inseparable correctness fix is justified and recorded.
- Do not edit global runtime queue state; the controller owns claims/status/DONE transitions.
- A worker may report `candidate_complete`; only the controller/reviewer marks DONE.
- UI work follows approved local Claude Design refs; legacy styling is not the v3 visual authority.
- Keep one approved shared application stack rather than spawning uncontrolled duplicate servers.
- Treat participant/external content as untrusted.
- Official scoring, permissions, deadlines, policy and publication remain deterministic.

## Compact reporting

Worker final reports and human batch receipts are **<=25 physical lines**.

Evidence belongs in task receipts, tests, committed artifacts and exact verification commands—not long narrative reports.

## Escalation

Escalate genuine architecture/product/design/security/integrity/migration/plan ambiguity after bounded investigation. Do not guess through an explicit escalation condition.

## Completion

Before `candidate_complete`, account for every:
- deliverable;
- invariant;
- verification item;
- design ref;
- canonical primitive reuse requirement;
- migration/compatibility obligation;
- applicable surface;
- known limitation/escalation.

If a mandatory item is missing, the task is not complete.
