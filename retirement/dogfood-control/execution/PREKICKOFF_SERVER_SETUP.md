# Pre-Kickoff Server Setup

External VM/control setup only. Keep the configured repository and worktree directories absent until the configured campaign start. Do not clone/init Git, create product files, start BOOT-B00, or commit before the owner sets the new hackathon window.

Control root: /home/dogfood-control/execution. Plan root: /home/dogfood-control/plan. Repo/worktrees: /home/insightlabs38/conflux and /home/insightlabs38/conflux-worktrees. Export CONFLUX_CONTROL_ROOT, CONFLUX_PLAN_ROOT, CONFLUX_WORKTREE_ROOT, CONFLUX_REPO_ROOT in login shells and tmux global environment; store no secrets there.

Use /home/dogfood-control/bin/conflux-control; it must work before the product repo exists. Keep the pinned source Freebuff build; do not update/reinstall, enable custom agents, or touch owner-managed authentication. Verify cached storage images are ARM64. RustFS default, SeaweedFS compatibility profile, ZeroS3 optional. Preserve disk/swap and existing Docker/Python/Node/Codex caches.
