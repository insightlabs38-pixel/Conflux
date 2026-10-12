# Agent Logistics and Orchestration

## Human-visible control plane

- Claude Code / Sonnet 5: architecture-heavy, security/concurrency/math, hard debugging, high-risk coherent batches and large gates.
- Codex CLI / GPT-6 Sol by default: large coherent implementation, cross-stack integration, ordinary hard engineering; Luna is cheap auxiliary/review/overflow where useful.
- Freebuff Orchestrator / GLM 5.3 Flash: queue scheduler and worker pool manager.

## Freebuff topology

The visible orchestrator is a manager, not a product-code implementer. For simultaneous writers, launch separate Freebuff CLI worker processes in separate Git worktrees through wrapper scripts; do not let several editing subagents share one worktree/index. Native spawned agents may be used for bounded read-only analysis/review if useful.

## Initial concurrency

- 1 Claude batch
- 1 Codex batch
- 3–4 Freebuff implementation workers
- 1–2 Freebuff verification/review workers

Increase only when ready-queue depth is healthy and merge/review/integration latency remains low.

## Scheduler priority

P0/P1 blockers → required Core dependencies → tasks that unlock many downstream nodes → judging/adoption hero work → Core polish → Stretch → Very Stretch. Do not keep agents busy artificially.

## Canonical state

Only the orchestrator/integration control process mutates canonical queue state. Workers return receipts; they do not race to edit `TASKS.yaml`.


## Senior next-batch behavior
Normal Claude/Codex invocations select the next eligible lane-appropriate batch automatically using `NEXT_BATCH_SELECTION.md`. Explicit batch IDs are reserved for deliberate out-of-order work and escalation/remediation.

## Session isolation
Only the Freebuff orchestrator/control layer may launch/manage Freebuff worker processes. It must not control Claude/Codex sessions. Individual workers and senior sessions must not call, message, resume, terminate or inspect private state from other running sessions.
