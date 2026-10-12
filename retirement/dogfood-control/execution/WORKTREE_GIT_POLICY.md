# Worktree and Git Policy

After the configured campaign start, canonical repo is `/home/insightlabs38/conflux` and isolated worktrees are `/home/insightlabs38/conflux-worktrees`. Both locations are writable by the service account. The campaign schedule must be configured before any clone or product branch is created.

Branch examples: claude/<batch-id>, sol/<batch-id>, luna/<task-id>, freebuff/<task-id>, fix/<id>. Clearly distinguish Sol from Luna.

Senior sessions own coherent batch branches; bulk sessions own one task branch/worktree per lease. Reservations record lane, ID, branch, worktree, start timestamp and optional session ID. Never share an index/worktree among writers. Use conflux-control for claims and transitions.
