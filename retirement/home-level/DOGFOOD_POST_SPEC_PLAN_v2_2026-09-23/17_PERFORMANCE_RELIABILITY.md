# Performance, Reliability and Deadline Bursts

## Critical writes
Draft save, submission finalization, ballot submit, community vote and advancement decisions.

## Finalization
Small transaction; row lock/constraints; server deadline; idempotency; no remote I/O.

## Data/query discipline
Indexes on event/status, stage/status, evaluation/judge/status and common gallery filters. Avoid expensive live aggregates in organizer dashboards; precompute/cache read-heavy summaries safely.

## Load scenarios
- baseline
- deadline_storm
- judging_open
- voting_spike
- gallery_spike

Provisional performance targets are engineering budgets, not claims: cached public reads <100ms p95, normal API reads <200ms, draft/finalize/ballot/vote within low hundreds of ms on the documented reference VM where practical, error rate <0.1% under defined load. Correctness invariants take precedence.

## Graceful degradation
Valkey loss may reduce caching/rate-limit quality but not corrupt authoritative state. Worker/webhook failures remain retryable. App restart preserves DB/object-store state.

## Backup/restore
Core includes operator scripts and a restore smoke test. Do not claim production-grade HA from a single-laptop Compose stack.
