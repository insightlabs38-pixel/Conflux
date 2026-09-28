# Capacity and load testing

## Sizing

- `UVICORN_WORKERS` (default 2) sets worker processes; each is one CPU-bound Python process.
- `CONFLUX_MAX_INFLIGHT_REQUESTS` (default 12) caps requests executing at once per worker. Every executing request holds one PostgreSQL connection (`CONN_MAX_AGE=0`), so peak connections ≈ `workers × cap` plus Celery. Keep it under `max_connections` (100 by default). Excess requests queue instead of failing; `/api/v1/health/` bypasses the queue.
- Measured on an 8-core host against PostgreSQL 17 (300 finalized projects, 30 judges): about 105 req/s with 2 workers and 185 req/s with 4 on the mixed workload. Raise workers before raising the cap.

## Reproducing

`loadtests/h02/run.sh OUT_PREFIX` resets a scratch database, seeds a 400-participant event, serves it with uvicorn, drives a mixed workload (public gallery/search, participant autosave/finalize/vote, judge draft/ballot, organizer progress, normalization and results) plus same-resource races, and reconciles the database against the responses. `WORKERS`, `SECONDS_`, `SCALE` tune it. `loadtests/h02/profile_queries.py` prints per-endpoint query counts and DB time. Results: `docs/verification/PVS-H02/`.
