# Freebuff Serial Bulk Task Protocol

Freebuff is one serial top-level bulk lane. Normal model: GLM 5.3 Flash. Consume one READY bulk task at a time using conflux-control next-task freebuff, then atomically claim it. Keep at most one active top-level TUI; create a fresh instance only after the current usage-limited session has completed its active task.

Keep one Freebuff TUI session across serial tasks while its usage window remains active. After each task has a completion receipt and integration is handled, claim the next eligible unit and send its standard task prompt into the same session. Use one stable, dedicated Freebuff worktree path and rotate its branch only after integration, so the live TUI stays rooted in the isolated Freebuff workspace. The 50-minute mark is informational; it is not a timeout. When Freebuff shows its ended-session UI (`Session ended` and `Press Enter to continue in a new session`), never press Continue. If a task is still running, let it finish and produce its receipt first. Then close the old TUI; start a fresh instance for the next task. If the session ends before the active task has a receipt, preserve its lease/worktree/handoff and resume that same task in a fresh instance; do not claim another task. Actual account quota/auth errors remain paused until availability is confirmed; they must not be retried by repeatedly opening fresh sessions.

Provider-supplied built-in helpers exposed by the installed working version may assist inside this session with code search, file discovery, web/docs research, shell/bash or review/thinking. This does not authorize custom user-defined agents. Custom agents are disabled because the current provider returns HTTP 403. Do not invoke them or try to repair the provider failure.

Never control Claude/Codex, type into another agent's tmux pane, or inspect another agent's private transcript. Never mutate canonical queue/ownership YAML directly; use conflux-control or explicit human/integration recovery.

DeepSeek V4.1 Flash spends Freebucks and requires explicit owner authorization or an explicitly owner-approved rule. Never spend Freebucks autonomously. GPT-6 Luna through Freebuff is contingency routing, not default.

Retry policy: one GLM attempt and one bounded correction only for a clearly mechanical defect. If reasoning-limited, seek owner-authorized DeepSeek or escalate by problem class to Luna/Sol/Claude. Leave a concise receipt with lane, model, worktree, focused tests and outcome.
