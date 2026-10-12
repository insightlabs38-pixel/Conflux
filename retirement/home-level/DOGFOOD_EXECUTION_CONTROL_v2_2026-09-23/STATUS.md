# Human Status Surface

`make status` or equivalent external control script should summarize:
- integration runtime health/mode;
- Core gates T1/T2/T3/T4/core/release;
- active Claude/Codex batch;
- active Freebuff tasks/worktrees;
- ready/blocked/review/correction/escalation counts;
- ATTENTION items;
- last green main commit/last merge;
- verification campaign status;
- model/reset/VM capacity notes when manually supplied.

Avoid building a large orchestration application; a small script reading YAML/Git/health endpoints is sufficient.
