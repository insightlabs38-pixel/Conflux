# Codex CLI Campaign Protocol — Automatic Next Batch

Normal invocation means **work the next eligible Codex batch**. The owner names a batch only for an intentional out-of-order assignment or escalation/remediation.

## Selection
Reconstruct state from `CURRENT_STATE.md`, `BATCHES.yaml`, `TASKS.yaml`, `OWNERSHIP.yaml`, `DECISIONS.md`, and `SESSION_HANDOFF.md`. If no explicit batch is named, scan batches in file order and select the first incomplete batch whose dependencies/gate are satisfied, which is unclaimed/nonconflicting, and whose preferred executor is Codex/Sol (or is explicitly marked Codex-compatible by control state). If none is safe, stop.

## Session isolation
Do not message, resume, stop, inspect private interactive state from, or call another Claude/Codex/Freebuff session. Do not invoke other coding agents or subagents. Never type into another tmux agent pane. Coordinate through Git/control state/receipts and the owner/orchestrator only.

## Targeted retrieval
Use `rg` first, then `grep`/`git grep`, `sed -n` ranges, `git show`, `git diff`, and path-scoped history before whole-file reads. Read an entire large file only when full-file semantics are actually necessary. Avoid recursive planning/history rereads.

## Execution
Execute one coherent batch, respecting task dependencies, ownership, frozen primitives, offline operation, server-side authorization/deadlines, idempotent critical writes, audit/outbox, and compatibility/version contracts. Add focused implementation tests; leave broad fuzz/permutation matrices to Freebuff. Run relevant lint/type/build/tests, produce concise evidence, commit/push, and stop after the selected batch.
