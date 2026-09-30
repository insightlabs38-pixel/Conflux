# SINGLE-AGENT IMPLEMENTATION PROMPT — Defined Task

You are the sole implementation agent for one assigned Conflux Product Depth v3 task.

Assigned task:

`TASK_ID={{TASK_ID}}`

Optional run metadata:
- worker/session: `{{WORKER_ID}}`
- model: `{{MODEL}}`
- branch/worktree: `{{BRANCH_OR_WORKTREE}}`

You are not acting as a multi-agent orchestrator. Do not spawn or manage implementation workers unless the owner explicitly authorizes that separately. You are responsible for understanding, implementing, verifying, documenting, and preparing this one task for completion.

## 1. Load bounded task context

From the repository root:

```bash
python scripts/pdv3/task_context.py "{{TASK_ID}}"
git status --short
git branch --show-current
```

Read the assigned task, batch, referenced subsystem specs, design refs, primitive contracts, and the current implementation/tests relevant to the task.

Use targeted repository inspection freely:
- `rg`
- `grep`
- `sed -n`
- `head`
- `tail`
- narrow `find`
- exact file reads
- targeted edits to `TASKS.yaml` / `BATCHES.yaml` where the task explicitly requires planning corrections

Large YAML files are not a problem when accessed surgically. Avoid only dumping irrelevant large ranges, generated SDKs, lockfiles, giant logs, or whole directories into context.

## 2. Authority order

Use this order when requirements overlap:

1. assigned task fields:
   - `deliverables`
   - `invariants`
   - `verification`
   - `non_goals`
   - `reuses`
   - `surface_matrix`
   - `design_refs`
2. referenced subsystem specification(s);
3. `docs/product-depth-v3/EXECUTION_PRINCIPLES.md`;
4. `docs/execution-v3/COMPLETION_RULES.md`;
5. canonical primitive/design contracts;
6. current correct repository behavior and tests.

If two controlling requirements materially conflict, investigate with bounded effort and use the escalation protocol. Do not silently invent a compromise.

## 3. Implement the complete task

A task is not complete because:
- a model field exists;
- an endpoint returns;
- a component renders;
- a settings toggle exists;
- the happy path works;
- a focused test passes.

Implement the workflow and depth required by the task/spec.

You must:
- reuse canonical primitives listed in `reuses`;
- avoid parallel/local truth models;
- preserve server-side authorization, audit, versioning, lifecycle and validation;
- handle migrations/compatibility when persisted or external contracts change;
- implement required error/empty/loading/permission/dense/mobile/offline/concurrency states where applicable;
- preserve progressive disclosure so expert features do not make the default product harder to use;
- preserve deterministic authority for scoring, permissions, deadlines, policy and publication.

Do not add unrelated frameworks or cleanup.

## 4. UI/design implementation

If `design_refs` apply, treat the approved local Claude Design handoff as concrete implementation authority.

Preserve:
- hierarchy;
- density;
- interaction order;
- visible state;
- responsive behavior;
- component semantics;
- accessibility;
- dark/light behavior where applicable.

Do not reinterpret Ledger into generic SaaS.

Avoid:
- giant marketing heroes in operator workflows;
- gradients as decoration;
- card oceans;
- nested cards;
- oversized KPI tiles;
- excessive pills/badges;
- large dead whitespace;
- icon-in-colored-square repetition;
- desktop squeezed onto mobile.

Do not sacrifice correctness or accessibility for pixel similarity.

## 5. Repository and Git safety

Inspect current Git state before editing.

Do not:
- `git reset --hard`;
- `git clean` away unowned work;
- blanket checkout/revert unrelated files;
- force-push;
- rewrite unrelated history;
- discard another session's work.

Stay within task ownership where practical.

A small inseparable correctness fix outside nominal ownership is allowed if it is necessary and recorded. Escalate before a large cross-domain rewrite.

## 6. Debugging discipline

- Fix root causes.
- Do not weaken tests or gates to obtain green output.
- Do not raise timeouts blindly to conceal races/performance defects.
- Do not fabricate screenshots, benchmark results, service responses, or verification evidence.
- Prefer canonical services/APIs over direct database patching.
- Treat participant-authored, rich, uploaded and external content as untrusted.
- Do not start uncontrolled duplicate application stacks if an approved shared stack exists.

If the task exposes a pre-existing unrelated defect, record it separately rather than silently absorbing it unless it blocks correct implementation.

## 7. Verification

Execute every required verification item that can be executed in the environment.

Also run the smallest appropriate adjacent regression set.

Examples:
- backend/domain task → focused tests + affected integration tests;
- UI task → component/browser/state checks + approved reference comparison;
- migration task → forward migration + compatibility/backfill evidence;
- archive/Event-as-Code task → version/round-trip/stale-plan behavior;
- judging/results task → deterministic frozen-input regression cases;
- performance task → before/after evidence, not intuition.

Record exact commands and actual results.

An unexecuted check is not a pass.

## 8. Completion check

Before reporting candidate completion, account for every:

- `deliverables` item;
- `invariants` item;
- `verification` requirement;
- required design reference;
- canonical primitive reuse requirement;
- migration/compatibility obligation;
- applicable surface;
- known limitation/escalation.

If a mandatory item is missing, the task is not complete.

## 9. Receipt

Write/update:

`docs/execution-v3/receipts/tasks/{{TASK_ID}}.yaml`

using `docs/execution-v3/RECEIPT_SCHEMA_V3.yaml`.

Then run:

```bash
python scripts/pdv3/lint_receipt.py "docs/execution-v3/receipts/tasks/{{TASK_ID}}.yaml"
```

Use `status: candidate_complete` only if the full completion check passes.

If blocked, use the appropriate blocked/corrections state and create an escalation when required.

## 10. Commit

Commit coherent work to the assigned/current task branch if repository policy permits.

Do not alter global runtime queue state unless this task explicitly assigns queue-control responsibility.

## 11. Final report — hard limit: 25 physical lines

Your final report must be **<=25 physical lines**.

Include only:
- task ID and candidate status;
- high-value changes;
- commit SHA if applicable;
- key verification commands/results;
- receipt path;
- limitations;
- escalation/blocker if any.

Do not paste logs or restate the task specification.

The task should be left in a state where another reviewer can determine completion from repository evidence without relying on your chat context.
