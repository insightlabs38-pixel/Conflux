# Checkpoint and Handoff Protocol

## Program checkpoint

A checkpoint is a compact recovery snapshot, not a progress essay.

Create one:
- after every completed batch;
- at a major gate;
- before deliberate controller shutdown;
- after a P0/P1 resolution;
- after a major approved design/spec revision;
- when active parallel work would otherwise be expensive to reconstruct.

Store:
`docs/execution-v3/checkpoints/<CHECKPOINT-ID>.yaml`

Update:
`docs/execution-v3/checkpoints/CURRENT.yaml`

## Worker handoff

If a worker stops before candidate completion but can still write state, it creates:
`docs/execution-v3/handoffs/<TASK-ID>.yaml`

Use `HANDOFF_SCHEMA.yaml`.

The handoff is for continuation, not justification. It should identify the exact safest next action.

## Batch human report

The batch receipt is the human-readable checkpoint summary and stays <=25 physical lines.

## No duplicate narrative

Do not maintain the same decision independently in:
- controller chat;
- checkpoint;
- handoff;
- receipt;
- spec.

The controlling spec/decision file is authoritative; the other artifacts point to it.
