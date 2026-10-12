# Recovery and Reboot

Persist: control pack/state, repo/worktrees, Git credentials/config, model CLI auth, Postgres/object-store volumes once created, tmux config and logs. Do a pre-kickoff deliberate reboot/reconnect rehearsal using only scratch infrastructure.

During event, recovery target is: reconnect → inspect status → restore tmux/control → `git status`/fetch → health-check integration stack → resume claimed workers or mark stale claims for recovery. Never guess ownership after a crash; reconcile leases/branches first.
