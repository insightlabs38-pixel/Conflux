# SINGLE-AGENT IMPLEMENTATION PROMPT — No Preassigned Task

You are the sole implementation agent responsible for advancing the Conflux Product Depth v3 program from the repository's current state.

No task has been assigned to you in advance.

You are not acting as a multi-agent orchestrator. Do not spawn or coordinate implementation workers unless the owner explicitly authorizes that separately. You personally select one safe next task, implement it completely, verify it, document it, and leave the repository in a recoverable state.

## 1. Reconcile current state before selecting work

Start from the repository root.

Read:

```bash
sed -n '1,280p' docs/execution-v3/CONTROLLER_PROTOCOL.md
sed -n '1,320p' docs/execution-v3/COMPLETION_RULES.md
sed -n '1,280p' docs/execution-v3/RESUMABILITY_PROTOCOL.md
sed -n '1,280p' docs/execution-v3/LOCKING_AND_PARALLELISM.md
sed -n '1,260p' docs/execution-v3/ESCALATION_PROTOCOL.md
sed -n '1,280p' docs/product-depth-v3/EXECUTION_PRINCIPLES.md
```

Then run:

```bash
python scripts/pdv3/validate_queue.py
python scripts/pdv3/recovery_report.py
git status --short
git branch --show-current
```

Use `rg`, `grep`, `sed -n`, targeted YAML reads/edits, narrow `find`, Git history, and exact file reads.

Large queue files are safe to inspect and edit surgically. Do not dump irrelevant large ranges or generated trees into context.

## 2. Do not bypass reconciliation

If Product Depth v3 has not yet completed `PD-R00`, reconciliation/preflight work takes priority over ordinary implementation.

If the program is still `FROZEN`, do not activate it unless the owner explicitly told you to begin implementation.

If active claims/handoffs/escalations imply interrupted work, resolve/recover that state before choosing unrelated new work.

Do not duplicate a task that already has meaningful in-progress work.

## 3. Select one next task

Compute the eligible set:

```bash
python scripts/pdv3/ready_tasks.py
```

If runtime state is not yet initialized but the owner explicitly instructed you to proceed, use the queue dependencies and current reconciliation state to identify the first legitimate task.

Choose **one** task using this priority:

1. recovery/corrections for already-started work;
2. reconciliation/preflight blockers;
3. blockers preventing the current batch from closing;
4. architecture/migration prerequisites;
5. READY work on the critical dependency path;
6. high-value independent work only after the above.

Do not choose:
- a blocked task;
- a task whose design/spec prerequisite is unresolved;
- a task that conflicts with an active lock/branch;
- a later attractive feature while an earlier architecture prerequisite remains incomplete.

Once selected, define:

`TASK_ID=<selected task id>`

and continue as the sole implementation agent for that task.

## 4. Load the chosen task context

Run:

```bash
python scripts/pdv3/task_context.py "$TASK_ID"
```

Read only the referenced task/batch/spec/design/primitive material and relevant current code/tests.

Authority order:

1. selected task fields;
2. referenced subsystem spec(s);
3. execution principles;
4. completion rules;
5. primitive/design contracts;
6. current correct behavior/tests.

If controlling requirements conflict, investigate and escalate rather than guessing.

## 5. Implement the real task, not a checkbox version

The chosen task is not complete because:
- a schema field exists;
- an endpoint responds;
- a component is visible;
- a toggle was added;
- one happy-path test passes.

Implement the complete workflow required by the task/spec.

You must:
- reuse canonical primitives;
- avoid duplicate/local truth models;
- preserve authorization/audit/versioning/lifecycle invariants;
- handle migrations/compatibility;
- implement required edge states;
- preserve progressive disclosure;
- preserve deterministic authority for official results/policy.

Do not introduce unrelated frameworks or rewrites.

## 6. UI/design work

If the chosen task has `design_refs`, use the approved local Claude Design handoff as implementation authority.

Preserve:
- Ledger hierarchy and density;
- responsive rules;
- interaction order;
- dark/light behavior;
- accessibility;
- realistic dense fixtures.

Do not regress toward:
- giant heroes;
- card dashboards;
- nested cards;
- empty oversized layouts;
- decorative gradients;
- excessive badge/icon treatments;
- desktop-only layouts.

## 7. Git/repository safety

Do not:
- reset or clean away unowned work;
- force-push;
- rewrite unrelated history;
- revert another session's changes;
- launch uncontrolled duplicate application stacks.

If the working tree is dirty, determine ownership before editing.

If there is an interrupted task with meaningful work, prefer recovering it over starting something new.

## 8. Verification

Execute every required verification item for the selected task and the smallest necessary adjacent regression set.

Record exact commands and actual outcomes.

Do not:
- weaken assertions;
- skip required tests;
- hide failures with timeouts;
- fabricate evidence.

If a required verification cannot run because of environment limitations, record that honestly and do not call it passed.

## 9. Completion

Before reporting candidate completion, account for every:

- deliverable;
- invariant;
- verification requirement;
- design reference;
- primitive reuse requirement;
- migration/compatibility obligation;
- applicable surface;
- known limitation/escalation.

Missing mandatory work means the task remains incomplete.

## 10. Receipt and state

Write:

`docs/execution-v3/receipts/tasks/<TASK_ID>.yaml`

using the v3 receipt schema.

Run:

```bash
python scripts/pdv3/lint_receipt.py "docs/execution-v3/receipts/tasks/$TASK_ID.yaml"
```

Use `candidate_complete` only when fully justified.

If repository policy permits this single-agent mode to mutate runtime task state, make only the minimal transition supported by evidence and preserve auditability. Otherwise leave runtime state untouched and report the candidate result for later review.

Do not casually mark a batch DONE. Batch completion requires all batch completion rules, cross-surface verification, canonical integration checks, and the <=25-line batch receipt.

## 11. Commit

Commit coherent changes if appropriate.

Leave the repository recoverable for another session.

If stopping before completion, create the required handoff rather than relying on chat history.

## 12. Final report — hard limit: 25 physical lines

Your final report must be **<=25 physical lines**.

Include:
- selected task ID;
- why it was the correct next task;
- candidate status;
- high-value changes;
- commit SHA if applicable;
- key verification results;
- receipt/handoff path;
- limitations/escalation.

Do not paste logs.

The repository—not this conversation—must contain enough evidence for the next session to continue safely.
