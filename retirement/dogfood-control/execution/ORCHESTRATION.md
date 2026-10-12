# Execution and Lane Control

There is no AI orchestrator. During the unattended window, the external supervisor launches isolated pinned model invocations and `/home/dogfood-control/bin/conflux-control` remains the deterministic authority for selection, atomic claims, reservations, status and reconciliation. Outside that window the owner coordinates sessions.

Senior batch lane: Claude local for hard reasoning; Codex GPT-6 Sol for coherent implementation/integration. Bulk task lane: Codex GPT-6 Luna at one active session initially; serial Freebuff GLM 5.3 Flash at one top-level task. Provider-built-in helpers may run inside the single Freebuff session; custom agents are disabled. Claude Code Cloud is owner-controlled reserve.

A bulk-eligible task in a Sol-preferred batch is available only when the batch is not reserved to a senior lane and paths are free. Senior reservation blocks conflicting bulk claims unless explicit split ownership is recorded.

Every mutation is serialized with OS flock and atomically written. Leases record lane, task/batch ID, branch, worktree, timestamp and optional session ID. Controller checks dependencies, phase/gates, path conflicts and Freebuff/Luna caps. Human-only gates cannot be auto-claimed. No product claim/work before the configured campaign start; the schedule is currently unset.
