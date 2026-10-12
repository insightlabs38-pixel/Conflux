# Session Isolation

Every coding-agent session is independent.

Workers MUST NOT:
- invoke another Claude/Codex/Freebuff coding agent;
- resume or terminate another agent's session;
- inspect another session's private transcript/context;
- send keystrokes/messages into another agent's tmux pane;
- commandeer another active worktree/branch/lease.

The only process allowed to manage Freebuff worker processes is the designated Freebuff orchestrator/control layer. Claude and Codex remain human-controlled lanes. Workers coordinate through integrated repository state, `OWNERSHIP.yaml`, task/batch state, receipts and escalation packets.
