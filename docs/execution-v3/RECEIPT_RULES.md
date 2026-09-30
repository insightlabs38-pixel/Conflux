# Receipt Rules

## Task receipt

Every mutating task writes:
`docs/execution-v3/receipts/tasks/<TASK-ID>.yaml`

Use `RECEIPT_SCHEMA_V3.yaml`.

Receipts must contain actual evidence. Do not write `pass` for an unexecuted check.

The task receipt is machine-oriented and may exceed 25 lines when the task has many deliverables.

## Batch receipt

Every completed batch writes:
`docs/execution-v3/receipts/batches/<BATCH-ID>.md`

**Maximum: 25 physical lines.**

Recommended format:

```md
# <BATCH-ID> — <title>
## Result
<1-2 lines>
## Changes
- <high-value change>
- <high-value change>
## Verification
- `<exact command>` → <result>
- `<exact command>` → <result>
## Limitations
- <honest limitation or "None known">
## Next
<next batch/gate>
```

Do not paste logs. Point to structured task receipts, committed artifacts or exact commands.

## Worker final report

The worker's final response to the controller is also <=25 physical lines and includes:
- task id;
- candidate status;
- commit;
- tests;
- receipt path;
- limitations/escalation.

The compact-report rule prevents long summaries from becoming a substitute for repository evidence.
