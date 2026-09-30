# Execution Lineage and Authority Map

Written by PD-R00-T01 (2026-09-30). One active authority; everything else is historical.

## Active (Product Depth v3)

| Role | Path |
|---|---|
| Future-work queue (plan) | `TASKS.yaml`, `BATCHES.yaml` (repo root) |
| Runtime state (controller-owned) | `docs/execution-v3/state/{PROGRAM,BATCH,TASK}_STATE.yaml` |
| Control protocol | `docs/execution-v3/**` (CONTROLLER_PROTOCOL, COMPLETION_RULES, RESUMABILITY, LOCKING, ESCALATION) |
| Product/depth/design contracts | `docs/product-depth-v3/**` (specs, primitives, design manifest r2.1) |
| Worker rules | `AGENTS.md`, `prompts/STANDARD_IMPLEMENTATION_PROMPT.md` |
| Single-agent run prompts | `docs/product-depth-v3/prompts/` (continuous, defined-task, no-task) |
| Tooling | `scripts/pdv3/*.py` |
| Scheduled Claude runner | `scripts/claude_supervisor/supervisor.py` (runs the continuous prompt; not a scheduler of tasks) |
| Receipts / claims / escalations | `docs/execution-v3/{receipts,claims,escalations,handoffs}/` |

Precedence: task fields > referenced specs > `EXECUTION_PRINCIPLES.md` > `COMPLETION_RULES.md` > primitives/design contracts > existing code.
Status precedence: runtime override in `state/` > status in `TASKS.yaml`/`BATCHES.yaml`.

## Historical (evidence and context only; never schedule work)

| Artifact | Meaning |
|---|---|
| `docs/execution/{TASKS,BATCHES}.yaml`, `README.md`, schemas | DOGFOOD v2 / UI-v2 queue; stale statuses are preserved verbatim. Interpret with `docs/batches/` and `docs/IMPLEMENTATION_CHECKPOINT.md`. |
| `docs/batches/*.md`, `docs/verification/**`, `docs/ui-v2/**` | Receipts and verification evidence for shipped work. |
| `master/`, `master.sh`, `tests/test_master_supervisor.py`, `.dogfood/` | DOGFOOD Claude/Codex master supervisor and its logs. Non-active; do not launch for v3. |
| `~/DOGFOOD_EXECUTION_CONTROL_v2_2026-09-23*`, `~/DOGFOOD_POST_SPEC_PLAN_v2_*` (outside repo) | Original external plan bundles and zips; docs/execution is the in-repo copy. |
| Branches `claude/C-B02`, `sol/C-B04`, `sol/BOOT-B00`, `freebuff/RT-001` and their `~/conflux-worktrees/*` | Old lane worktrees; fully merged into `main`, clean, not v3 claims. See PD-R00-T03 reconciliation. |
| `conflux_v3_claude_design_handoff*.zip` | Design handoff archives (untracked inputs); the extracted r2.1 handoff under `docs/product-depth-v3/design/` is what PD-DESIGN-B00 consumes. |

## Rules

1. Only `TASKS.yaml`/`BATCHES.yaml` at the repo root define v3 work; do not add another queue.
2. Legacy files are not rewritten except for a HISTORICAL banner pointing here.
3. Conflicting old instructions (single-sequential-worker, "authoritative queue", master polling) are void for v3.
