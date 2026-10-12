# Conflux — DOGFOOD 2026 Execution Manifest

Canonical queue totals (recalculated from YAML): **109 batches; 339 tasks**.

Batch preferred executors: bulk=50, claude-or-codex=5, claude-sonnet=13, codex-sol=40, human=1.

Task preferred executors: bulk=101, claude-or-codex=15, claude-sonnet=64, codex-sol=158, human=1. Bulk-eligible tasks: 285; excluded: 54.

This active package contains no custom Freebuff agents. Historical definitions are archived outside the package at `/home/dogfood-control/backups/freebuff-custom-agents-disabled/`.

Required lane/control documents include:
- AGENTS.md, ATTENTION.md, CURRENT_STATE.md, OWNERSHIP.yaml, ESCALATIONS.md
- BATCHES.yaml, TASKS.yaml, TASK_SCHEMA.md, RECEIPT_SCHEMA.yaml
- MODEL_ROUTING.md, ORCHESTRATION.md, NEXT_BATCH_SELECTION.md, NEXT_TASK_SELECTION.md
- CLAUDE_CODE_PROTOCOL.md, CODEX_CLI_PROTOCOL.md, CODEX_LUNA_TASK_PROTOCOL.md
- FREEBUFF_PROTOCOL.md, FREEBUFF_ROLES.md, FREEBUFF_RECOVERY.md
- CODEX_CAPACITY_PROBE.md, CLAUDE_CLOUD_RESERVE.md, VERIFICATION_CAMPAIGNS.md
- KICKOFF_BOOTSTRAP.md, PREKICKOFF_SERVER_SETUP.md, LUNA_VM_SETUP.md
- WORKTREE_GIT_POLICY.md, SESSION_ISOLATION.md, STATUS.md, RECOVERY.md
