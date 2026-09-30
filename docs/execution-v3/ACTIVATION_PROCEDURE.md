# Activation Procedure

The bundle is shipped **FROZEN**.

Claude Design foundation work may be run while the program is frozen. Stabilization implementation begins only after explicit activation.

## Preconditions

From repository root:

```bash
python scripts/pdv3/validate_queue.py
python scripts/pdv3/recovery_report.py
```

Required:
- queue validation passes;
- no unexplained active claim from an earlier campaign;
- canonical Git working tree is understood/clean enough for controlled activation;
- Stage B specs/primitives/design protocol are present;
- owner has deliberately approved starting Product Depth v3.

Claude Design does **not** need to be complete before `PD-B00` starts. The DAG intentionally blocks the visual foundation at `PD-DESIGN-B00`.

## Activate

Dry run:

```bash
python scripts/pdv3/activate.py
```

Apply:

```bash
python scripts/pdv3/activate.py --apply --confirm PRODUCT-DEPTH-V3
```

Activation:
- changes `PROGRAM_STATE` from FROZEN to ACTIVE;
- increments controller epoch;
- records canonical commit;
- promotes `PD-R00` to IN_PROGRESS;
- promotes dependency-satisfied entry task(s) of PD-R00 to READY in runtime state.

It does **not** rewrite the full `TASKS.yaml` / `BATCHES.yaml`.

## First controller action

```bash
python scripts/pdv3/ready_tasks.py
python scripts/pdv3/task_context.py <READY-TASK-ID>
```

Then create the claim/worktree and launch the standard implementation prompt.

## Pause

A controller may set `PROGRAM_STATE` to `PAUSED` after checkpointing. PAUSED means:
- do not launch new mutating work;
- active workers may be allowed to reach a safe handoff/receipt;
- resume requires recovery reconciliation.

## Never activate by editing one `BLOCKED` string manually

Use the runtime-state procedure so activation is deliberate, reviewable and reversible without mass YAML churn.
