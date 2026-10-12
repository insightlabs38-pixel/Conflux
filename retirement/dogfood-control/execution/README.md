# Conflux — DOGFOOD 2026 Execution Control

External control pack, not submission code. The campaign is locked until a start and end are deliberately configured. Use `/home/dogfood-control/bin/conflux-schedule set START_UTC END_UTC` to schedule it, or `conflux-schedule clear` to leave it unscheduled. No campaign time is currently configured. The timer is disabled until a schedule is set.

Claude and Codex GPT-6 Sol use the senior batch lane. Codex GPT-6 Luna and serial Freebuff GLM use the bulk task lane. Freebuff is one top-level session, not an orchestrator. Provider-built-in helpers may assist internally; custom agents are disabled. Claude Cloud is owner-controlled reserve.

The external conflux-control tool serializes queue state changes and provides status, safe next selection, atomic claims, release/review/done/block/reserve and reconciliation. Relative control references use CONFLUX_CONTROL_ROOT; plan references use CONFLUX_PLAN_ROOT. Queue counts are in MANIFEST.md and recalculated from canonical YAML.
