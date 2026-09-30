# PD-B02 results (before/after, same host, 8 cores)

| Measure                            | PD-B00 baseline                        | After PD-B02                                                                           |
| ---------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------- |
| SQLite `pytest -n auto` wall / CPU | 78 s / 9m12s (1400 passed, 23 skipped) | **22 s** with `--dist worksteal` (25 s with `load`) / ~2m27s (1404 passed, 23 skipped) |
| PostgreSQL 17 wall                 | 97 s (1418 passed, 5 skipped)          | **44 s** (1423 passed, 4 skipped), 5/5 consecutive runs clean                          |
| Slowest test call                  | 7.0 s (CSRF login throttle, PBKDF2)    | 2.1 s (`test_route_sweep` adversarial bodies)                                          |

Changes: (1) test-only MD5 hasher via `tests/conftest.py` + `tests/security/test_password_hashing_fidelity.py` (production hasher default PBKDF2 asserted; end-to-end login with it); (2) `make test` uses `--dist worksteal` (22 vs 25 s over 3 paired runs: `logs/T03-dist-compare.log`); (3) `test_route_sweep` module fixture leaked committed workspaces/users, which made `test_demo_scenarios` fail ~1 in 3 PostgreSQL runs under `worksteal` scheduling (deterministic repro: route_sweep then demo_scenarios) — fixed by cleanup in teardown plus a conftest leak detector (proved to fail the module when cleanup is removed).
Equivalence: no test removed (`comm` of collected ids vs e1888de: 0 removed; new tests: 3 hasher guards, 1 fixture hash pin, 1 upgrade smoke). Skip set unchanged on SQLite (23) and reduced on PostgreSQL (upgrade smoke now runs). Not changed: per-worker migration setup (~7 s, 101 migrations); `--nomigrations` breaks 1 test, template-copy reuse would save ≈ 6 s of 22 s and adds infrastructure — deferred as not warranted.
