# Unattended handoff

Updated: 2026-09-25 22:24 UTC

- Campaign: not scheduled. Start/end settings are intentionally blank following the one-day delay.
- Timer/service: disabled/inactive. No workers were relaunched.
- Bootstrap: not started; no local clone, product files, receipts, or task claims.
- Remote: `https://github.com/insightlabs38-pixel/Conflux`; prior logs show GitHub preflight passed and the clone failed at local directory creation.
- Root cause fixed in the launch configuration: repo and worktrees now live under `/home/insightlabs38`, which the service account can write.
- Retry behavior fixed: a preflight failure is logged and exits successfully, so systemd no longer restarts it every 30 seconds.
- To configure the delayed event window later: `/home/dogfood-control/bin/conflux-schedule set START_UTC END_UTC`. The end must be at least 20 minutes after the start; claims stop 10 minutes before end.
- Logs: `/home/dogfood-control/logs/unattended/`; the 453 historical retries remain available in `supervisor.jsonl`.
