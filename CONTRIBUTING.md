# Contributing

Run `make verify-fast` before submitting a change. Add focused tests alongside
behavior changes and keep secrets, generated databases, and dependency caches
out of Git.

## Backend test feedback targets

Measured 2026-09-30 on 8 cores (`docs/verification/PD-B02/`): `make test` backend suite ≈ **22 s** on SQLite and ≈ **44 s** on PostgreSQL 17 (`DATABASE_URL=postgres://… uv run pytest -n auto --dist worksteal`). Targets: keep the SQLite run under **30 s** and PostgreSQL under **60 s**; investigate before either grows by more than 25%.

- Tests use a fast password hasher (`tests/conftest.py`); production hashing is guarded by `tests/security/test_password_hashing_fidelity.py`. Do not create users with a production hasher in bulk.
- A module-scoped fixture that commits data (via `django_db_blocker.unblock()`) must delete it in teardown; the conftest leak detector fails the module otherwise.
- About 7 s of every xdist worker is migrating its test database (101 migrations); avoid adding migrations that are slow to apply.
