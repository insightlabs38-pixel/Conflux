# Claude Code Campaign Protocol — Automatic Next Batch

Normal invocation means **work the next eligible Claude batch**. The owner names a batch only when intentionally overriding queue order or assigning an escalation/remediation batch.

## Selection
1. Reconstruct current state from `CURRENT_STATE.md`, `BATCHES.yaml`, `TASKS.yaml`, `OWNERSHIP.yaml`, `DECISIONS.md`, and `SESSION_HANDOFF.md`.
2. If the owner explicitly names a batch, use that batch after verifying it is safe to claim.
3. Otherwise scan `BATCHES.yaml` in file order and choose the first batch that:
   - is not complete;
   - has every dependency complete;
   - belongs to an unlocked phase/gate;
   - is not ACTIVE/reserved/leased to another worker;
   - has no conflicting owned-path lease;
   - is appropriate for Claude (`preferred_executor: claude-sonnet` first; Claude-compatible high-risk batch may be selected only when queue/control state explicitly permits).
4. If no safe eligible batch exists, report that and stop. Never steal another session's batch.

## Session isolation
- Do not communicate with, prompt, resume, terminate, inspect interactive conversation state from, or otherwise control another Claude/Codex/Freebuff session.
- Do not invoke another coding agent, subagent, Claude, Codex, or Freebuff from this session.
- Do not use tmux to type into another agent pane.
- Coordinate only through Git, queue/control files, receipts, and owner/orchestrator-provided state.
- Reading ordinary repository files created by integrated work is allowed; reading another agent's private scratch/session transcript is not.

## Targeted retrieval is mandatory
Before reading a whole nontrivial file, use targeted search/range inspection first unless complete-file semantics are genuinely required. Prefer, in order: `rg`, `grep`/`git grep`, `sed -n 'START,ENDp'`, `git show`, `git diff`, `git log -- <path>`, then broader reads. Search the exact symbol/decision/task first; inspect the smallest useful surrounding range; expand only when necessary. Do not recursively reread planning/history or unchanged large files.

## Execution
- One invocation executes exactly one coherent selected batch.
- Preserve frozen architecture and task boundaries while reasoning/investigating freely inside them.
- Add focused tests that prove difficult semantics; high-volume fuzz/permutation breadth belongs to Freebuff.
- Run directly relevant checks; never weaken tests/permissions/deadline/migration/security invariants.
- If a new owner decision or foundational contradiction is required, minimize and escalate rather than guessing.
- Keep comments/reports concise; Git/tests are the detailed record.
- Finish the batch, inspect diff/scope, commit/push on the assigned branch, emit concise evidence, update authorized handoff/state, then stop. Do not continue to a second batch.
