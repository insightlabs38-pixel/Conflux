#!/usr/bin/env bash
set +e
cd /home/insightlabs38/conflux-worktrees/claude-C-B02
export DISABLE_AUTOUPDATER=1
unset OPENAI_API_KEY CODEX_API_KEY CODEX_ACCESS_TOKEN ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL
(set -o pipefail; (/home/insightlabs38/.npm-global/bin/claude --model claude-sonnet-5 --effort high --dangerously-skip-permissions --print --verbose --output-format stream-json 'CONTINUATION — do not reread the control pack. Read /home/dogfood-control/handoffs/claude/C-B02.md and the passive recovery bundle /home/dogfood-control/run/recovery/C-B02/snapshot.json; inspect git status and git diff --stat in /home/insightlabs38/conflux-worktrees/claude-C-B02; inspect only relevant diff/symbols; continue next actions from the latest agent-authored checkpoint while using controller observations as facts, not narrative. Keep branch claude/C-B02, worktree /home/insightlabs38/conflux-worktrees/claude-C-B02, unit C-B02. Do not claim another unit. Update handoff at meaningful boundaries and preserve receipt policy.') 2>&1 | /home/dogfood-control/bin/conflux-redact-log >> /home/dogfood-control/logs/unattended/claude-C-B02.jsonl) &
pid=$!
printf "%s\n" "$pid" > /home/dogfood-control/run/unattended-claude-c-b02.pid
wait "$pid"
rc=$?
printf "%s\n" "$rc" > /home/dogfood-control/run/unattended-claude-c-b02.exit
sleep 86400
