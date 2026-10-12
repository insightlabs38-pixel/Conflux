# Task Schema

Required fields: id, batch, phase, title, status, batch_dependencies, task_dependencies, goal, preferred_executor, bulk_eligible, risk, owned_paths, required_reading, acceptance, escalate_if.

preferred_executor is one of claude-sonnet, codex-sol, claude-or-codex, bulk, human. bulk_eligible is boolean and independent of preferred executor: ordinary medium work in a Sol-preferred but unreserved batch may be bulk eligible. High-risk and human-preferred tasks are always false. Authorization/security, concurrency, normalization/math and invariant tasks may be excluded even at medium risk. Ordinary low-medium and medium implementation/testing tasks are generally eligible.

The controller computes readiness from dependencies, gates, reservations and ownership. Human-only gates cannot be auto-claimed. IDs and dependencies are stable. Canonical queue updates go through conflux-control or explicit human recovery.
