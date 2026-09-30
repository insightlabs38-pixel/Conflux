# Resumability Protocol

The DOGFOOD campaign demonstrated that supervisor/worker processes can exit unexpectedly. Product Depth v3 treats process loss as a normal recovery case.

## Durable sources of truth

Recovery uses, in priority order:

1. canonical Git history;
2. `PROGRAM_STATE.yaml`;
3. latest checkpoint;
4. active claim files;
5. task branches/worktrees and their Git status;
6. task receipts;
7. worker handoffs;
8. open escalations;
9. task/batch plan files.

Chat history or a controller's remembered state is never required for correctness.

## Recovery classification

For each non-released claim, classify it as:

### A. Completed candidate
- receipt exists and says `candidate_complete`;
- branch has coherent commit(s);
- verification evidence exists.

Action: move to REVIEW; do not launch duplicate worker.

### B. Active/recoverable
- branch/worktree exists with meaningful unintegrated changes;
- no completion receipt.

Action: inspect handoff/Git diff and either resume the same task or assign a recovery worker to that branch.

### C. Claim only
- claim exists;
- no meaningful branch changes/receipt.

Action: release claim after verifying no live worker is still writing, then requeue.

### D. Integrated but state stale
- change is already on canonical integration history;
- task runtime state is not DONE.

Action: reconstruct verification/review evidence; never reimplement blindly.

### E. Conflicted/ambiguous
- multiple branches claim same task;
- lock collision;
- partial merge;
- unclear ownership.

Action: set task `ESCALATED` or `RECOVERING`; resolve before launching adjacent mutators.

## Worker interruption

A worker that can still write before stopping creates:
`docs/execution-v3/handoffs/<TASK-ID>.yaml`

The handoff records:
- current commit/worktree status;
- what was completed;
- what remains;
- failing verification;
- decisions made;
- files currently being edited;
- safest next command.

A replacement worker reads the task context + handoff + Git diff. It must not restart from scratch by default.

## Checkpoint cadence

Create a checkpoint:
- after every completed batch;
- at every major gate transition;
- before deliberate controller shutdown;
- after resolving a P0/P1 escalation;
- after a large design-contract revision;
- whenever several concurrently active claims would be costly to reconstruct.

Do not checkpoint merely to create paperwork.

## Stale heartbeat rule

A stale heartbeat is evidence that a worker may have stopped; it is **not** permission to launch a duplicate mutator.

The controller first checks:
- process/session if locally observable;
- worktree modification state;
- branch commits;
- receipt/handoff;
- lock ownership.

## Recovery must preserve uncommitted work

Never use destructive `git reset --hard`, blanket checkout, clean, or worktree deletion to "fix" a stale claim until the diff is inspected and either preserved, integrated, or explicitly discarded with evidence.
