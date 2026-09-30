# Runtime State Model

`TASKS.yaml` and `BATCHES.yaml` are the **plan** and remain stable enough to review/diff.

Runtime execution state is stored under `docs/execution-v3/state/` and claims/receipts. This avoids rewriting a 12+ MiB task registry for every heartbeat.

## Precedence

For task status:
1. runtime override in `state/TASK_STATE.yaml`;
2. otherwise task `status` in `TASKS.yaml`.

For batch status:
1. runtime override in `state/BATCH_STATE.yaml`;
2. otherwise batch `status` in `BATCHES.yaml`.

The queue's initial statuses remain `BLOCKED`; activation writes runtime overrides.

## Controller-only mutation

Only the controller changes:
- `PROGRAM_STATE.yaml`
- `TASK_STATE.yaml`
- `BATCH_STATE.yaml`

Workers write task branches, receipts, handoffs and escalations.

## Runtime statuses

Tasks:
`BLOCKED`, `READY`, `CLAIMED`, `ACTIVE`, `REVIEW`, `CORRECTIONS`, `ESCALATED`, `DONE`

Batches:
`BLOCKED`, `READY`, `IN_PROGRESS`, `REVIEW`, `DONE`, `ESCALATED`

## Promotion

READY is derived from dependencies but written as an explicit runtime transition for auditability.

The controller must re-evaluate readiness after every DONE/correction/escalation resolution.
