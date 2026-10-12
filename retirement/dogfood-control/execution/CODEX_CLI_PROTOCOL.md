# Codex GPT-6 Sol Senior-Batch Protocol

This protocol is for Codex GPT-6 Sol. Sol consumes coherent senior batches selected with `conflux-control next-batch sol` and reserved atomically with `claim-batch sol <id>`. Sol does not compete with Luna for individual task claims once a task is reserved.

If a Sol batch is reserved, bulk workers must not enter conflicting tasks in that batch unless the controller explicitly permits split ownership. Sol may handle difficult ordinary engineering, large coherent implementation batches, cross-stack integration, and major gates. Focused semantic tests belong with implementation; bulk verification breadth belongs to Freebuff/Luna. Do not control other model sessions or edit canonical YAML state directly. Record a concise receipt with lane, model, branch/worktree, verification and integration notes.
