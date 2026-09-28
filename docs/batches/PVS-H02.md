# PVS-H02 — Service load, query profiling and concurrency verification
## Result
A mixed workload (public browsing, participant autosave/finalize/vote, judge draft/ballot, organizer progress, normalization and results, plus same-resource races) runs cleanly against uvicorn + PostgreSQL 17 with no 5xx and no integrity violations. The run exposed one correctness risk, unbounded DB connections under bursts, and one product-blocking throttle, both fixed.
## Changes
- `config.concurrency.BoundedInflight` caps executing requests per worker (`CONFLUX_MAX_INFLIGHT_REQUESTS`, default 12; health bypasses). Before: 2 workers at full scale exhausted PostgreSQL (`too many clients`) and returned 500s; after: 0 errors, peak connections ≈ workers × cap.
- Authenticated voting is throttled per account, not per IP: a venue behind one NAT was capped at 30 votes/hour for the whole room.
- `loadtests/h02/` (seed, mixed driver, query profiler, `run.sh`) and `docs/operations/CAPACITY.md` (sizing, reproduction).
## Verification
- Full-scale saturated runs (156 actors): 2 workers 142 req/s, 4 workers 187 req/s, 0 server errors; DB reconciliation (ballots, votes, finalizations, audit, outbox, uniqueness) all PASS.
- Unsaturated (4 workers): p95 ≤ 130 ms on every write path; 70 same-resource races (8 concurrent each) → exactly one winner each, 0 violations.
- Query profile: flat counts, no N+1 (ballot submit 42 queries/21 ms, gallery 3 queries); indexes on hot lookups present. Evidence in `docs/verification/PVS-H02/`.
- Suite: SQLite 1199 passed/20 skipped; PostgreSQL concurrency+community 44 passed.
## Limitations
- Gallery is unpaginated (≈29 KB per 100 projects, ≈25 ms/300); revisit only if events exceed ~1000 projects.
- Load client is single-host Python, so it adds ≈40 ms floor to latencies; absolute numbers are conservative.
## Next
PVS18 not warranted (no throughput bottleneck at realistic surge). Proceed to PVS11.
