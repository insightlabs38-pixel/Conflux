# Freebuff Worker Protocol

The visible Freebuff orchestrator schedules unlocked tasks and may manage Freebuff worker processes; ordinary Freebuff workers do not manage or call other agents/sessions. Workers run in isolated task worktrees/branches.

All workers use search-first retrieval: `rg` → `grep`/`git grep` → `sed -n` ranges → Git diff/show/history before whole-file reads.

Implementation workers: read only task + required context; implement owned scope; add focused local tests; emit receipt; do not merge.

Verification workers: prefer generators/property/fuzz/matrices over repetitive tests; generate disposable corpora but commit only harnesses/minimized regressions; routine defects may get a bounded Freebuff correction; architecture/security/concurrency/data-integrity/weird persistent failures become escalation packets.

Session isolation: a worker never sends messages/keys to another worker or senior-model pane, resumes/terminates another session, or inspects another session's private transcript. Coordination is via queue/leases/Git/receipts.
