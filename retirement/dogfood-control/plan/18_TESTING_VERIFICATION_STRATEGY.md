# Testing and Verification Strategy

Implementation agents write focused tests that express feature semantics. Bulk verification lanes (Freebuff/Luna) own verification breadth: matrices, property tests, fuzzing, fixture mutation, malformed input, RBAC permutations, browser scenarios and routine load runs. Claude and Sol own critical semantic regressions, hard invariants and major gates.

Freebuff GLM provides continuous low-cost verification when its single top-level serial lane is not more valuable on implementation. Codex Luna can take parallel verification and fuzzing when the observed capacity probe supports it. Verification coverage does not shrink because the worker lane is serial or quota-limited.

The generic S3 adapter contract runs against RustFS and SeaweedFS. RustFS is the default runtime; SeaweedFS is an opt-in compatibility harness. ZeroS3 is an optional later target and never gates release. Keep provider tests about S3 behavior, not provider-specific application logic.

Verification campaigns remain focused and evidence-based: record command, scope, result, and any minimized regression in the receipt. Escalate authorization, concurrency, normalization/math, data-integrity and unexplained invariant failures to Claude or Sol.
