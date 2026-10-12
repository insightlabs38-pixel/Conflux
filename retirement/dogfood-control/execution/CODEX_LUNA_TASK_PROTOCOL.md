# Codex GPT-6 Luna Bulk Task Protocol

On normal invocation, run conflux-control next-task luna and atomically claim exactly one safe task. Do not select a senior batch. The selector requires satisfied dependencies, unlocked containing batch phase/gates, bulk_eligible true, task not DONE/ACTIVE/reserved, containing batch not exclusively reserved to a senior session and no path ownership conflict. Prefer Core over Stretch over Very Stretch, then dependency-unblocking tasks. Never select high-risk work. One task per invocation/session unless owner explicitly assigns otherwise.

Use targeted reading: rg, grep/git grep, sed ranges, git diff/show/history, whole-file only if needed. No interaction with other running agent sessions. Do not edit canonical queue/ownership state directly.

Write focused tests and provide a concise receipt with executor_lane, model, worktree, task ID, changed paths, verification command/results and blockers. Escalate security/authorization, concurrency, normalization/math and invariant uncertainty to Claude or Sol.
