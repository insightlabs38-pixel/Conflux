# Model and Lane Routing

## Senior batch lane
- Claude Code local: invariants, authorization/security, concurrency, normalization/math, root cause and gates; owner controls session.
- Codex GPT-6 Sol: large coherent implementation, cross-stack integration and difficult ordinary engineering.

## Bulk task lane
- Codex GPT-6 Luna: cheap fine-grained implementation/verification; one task per invocation; start with concurrency one and expand only from H0/H1 evidence.
- Freebuff: one serial top-level GLM 5.3 Flash task lane; built-in provider helpers may assist internally. Not an orchestrator.
- Freebuff DeepSeek V4.1 Flash requires explicit owner authorization because it spends Freebucks. GPT-6 Luna via Freebuff is contingency only.

Bulk workers do not enter senior-reserved batches without explicit split ownership. Eligibility does not reserve a task. Claude Code Cloud is owner-controlled reserve capacity in a separate environment; see CLAUDE_CLOUD_RESERVE.md.
