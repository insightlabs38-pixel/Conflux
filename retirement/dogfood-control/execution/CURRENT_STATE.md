# Current state — 2026-09-25 UTC

- Authoritative schedule is configured once in `/home/dogfood-control/unattended.env` (`CONFLUX_START_UTC`, `CONFLUX_END_UTC`).
- User timer is enabled, `Persistent=true`, and scheduled from that configuration. The unattended service is inactive until the timer fires.
- Startup state is `WAITING_FOR_START`. No bootstrap green marker, owned lease, or campaign model session is recorded.
- Handoffs live under `/home/dogfood-control/handoffs/{claude,sol,luna,freebuff}/`.
- Provider recovery commands are `conflux-control provider-status`, `provider-pause LANE`, and `provider-resume LANE` (`codex` aliases Sol).
- Freebuff keeps one TUI session across completed tasks while its usage window is active, sending each next assignment as a normal message. It holds one task lease at a time in a stable, dedicated Freebuff worktree and rotates the branch only after the prior task integrates. When the provider's ended-session limit UI appears, it lets any active task finish, then starts a fresh TUI for the next task; the 50-minute mark is informational only.
- Video queue and capture harness are operational demo assets. Capture waits for explicit Core gate or derived H48 insurance trigger and requires the application runtime.
- See `/home/dogfood-control/FINAL_PREKICKOFF_REPORT.md` and `/home/dogfood-control/execution/VIDEO_WORKSTREAM.md`.
