# Senior Next-Batch Selection

Claude and Sol select coherent batches with conflux-control next-batch claude|sol and reserve atomically before creating a worktree. Selection checks phase/gates, batch dependencies and owned paths. A senior reservation blocks conflicting bulk tasks unless explicit split ownership is recorded.

Luna/Freebuff use NEXT_TASK_SELECTION.md and do not take an entire senior batch because some child tasks are bulk eligible. Never race another reservation. Human promotion gates remain human-only.
