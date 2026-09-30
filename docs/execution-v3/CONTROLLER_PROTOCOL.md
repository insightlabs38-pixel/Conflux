# Controller / Orchestrator Protocol

## Authority model

The controller is the only process allowed to:
- choose READY work;
- create/expire claims;
- assign workers;
- arbitrate lock groups and overlapping mutation paths;
- integrate worker branches/worktrees;
- mutate runtime task/batch status;
- mark a task/batch DONE;
- promote downstream work.

Workers do **not** edit global queue/runtime state unless a controller task explicitly assigns that responsibility.

The controller itself must be disposable. No critical state may exist only in its chat/context/process memory.

## Startup procedure

On every fresh controller start or restart:

1. acquire the local controller mutex (`docs/execution-v3/state/controller.lock`) using an OS-level exclusive lock;
2. read `PROGRAM_STATE.yaml`;
3. run `python scripts/pdv3/validate_queue.py`;
4. run `python scripts/pdv3/recovery_report.py`;
5. inspect open claims, worktrees/branches, receipts, handoffs and escalations;
6. reconcile ambiguous claims before launching new work;
7. run `python scripts/pdv3/ready_tasks.py`;
8. select work only after lock/ownership checks.

Never assume the previous controller shut down cleanly.

## Pre-implementation reconciliation

On a fresh Product Depth v3 activation, complete `PD-R00` before `PD-B00`. Do not bypass reconciliation because the merged bundle appears visually clean.

## Work selection

Prefer work in this order:

1. recovery/corrections for already-active work;
2. blockers preventing an active batch from closing;
3. architecture/migration prerequisites;
4. READY tasks on the critical dependency path;
5. independent tasks that safely increase parallel utilization;
6. speculative/optional lanes last.

Do not start a task merely because it is listed earlier if a prerequisite contract is unresolved.

## Claim lifecycle

Before launching a worker, create:

`docs/execution-v3/claims/<TASK-ID>.yaml`

The claim records:
- task;
- batch;
- controller epoch;
- worker id;
- model/executor class;
- branch;
- worktree;
- lock groups;
- claimed_at;
- last_heartbeat;
- state.

Claim states:
`CLAIMED`, `ACTIVE`, `REVIEW`, `RECOVERING`, `RELEASED`.

Claim creation must occur before the worker edits code.

## Worktree/branch rule

Use one isolated worktree/branch per active mutating task unless the batch contract explicitly requires a single sequential workspace.

Recommended branch:
`pdv3/<TASK-ID-lowercase>`

Workers may commit to their task branch. They may not force-push, reset canonical main, rewrite unrelated history, or delete another worker's changes.

## Worker prompt

Every normal worker receives `prompts/STANDARD_IMPLEMENTATION_PROMPT.md` plus:
- TASK_ID;
- worker/model identity;
- branch/worktree;
- any controller-specific constraints.

The full queue is safe to maintain/edit with targeted tools, but workers should normally load only relevant queue context. Use:
`python scripts/pdv3/task_context.py <TASK-ID>`

Then read only referenced specs/design/current code required for the task.

## Integration

Before integration:

1. worker receipt is `candidate_complete`;
2. receipt lints;
3. changed paths match scope or have justified necessary spillover;
4. task verification evidence is real;
5. controller/reviewer checks completion rules;
6. rebase/merge against current integration state;
7. run conflict-sensitive verification after integration;
8. only then mark runtime task state DONE and release locks.

If integration reveals a regression, the task returns to `CORRECTIONS` or receives a new explicit repair task. Do not mark DONE and defer the known regression casually.

## Batch close

After all tasks are DONE:
- run batch T90/T91/T95 requirements;
- verify depth contract and surface matrix;
- run required canonical-main tests;
- create <=25-line batch receipt;
- checkpoint;
- mark batch DONE;
- promote newly unblocked batches/tasks.

## Controller crash

A controller crash is expected to be recoverable:
- claims remain on disk;
- branches/worktrees remain;
- worker receipts/handoffs remain;
- queue plan remains;
- runtime state/checkpoint remains.

The replacement controller follows `RESUMABILITY_PROTOCOL.md`. It must not simply release every old claim and launch duplicates.

## Controller reports

Controller human status reports are concise:
- <=25 lines unless the owner explicitly asks for a detailed audit;
- identify completed/in-progress/blocked work;
- link receipts/escalations rather than pasting logs;
- never claim a gate/test passed without exact evidence.

## No fake progress

Do not:
- create placeholder commits to increase completed counts;
- split one incomplete feature into many "done" sub-tasks while the promised workflow is unusable;
- mark design refs "satisfied" without approved local artifacts;
- mark tests skipped as passed;
- convert a product ambiguity into an arbitrary local decision when the spec requires escalation.
