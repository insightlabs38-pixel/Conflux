"""This directory holds two kinds of tests: genuine cross-connection
concurrency tests (need a real multi-connection-capable engine -- see each
such module's own `requires_real_db` skip condition, duplicated per module
since `tests/` isn't an importable package here) and static source checks
that need no database at all.

Point `DATABASE_URL` at a real PostgreSQL instance to run the former (see
docs/batches/C-B29.md for a disposable-container recipe); they're skipped,
not failed, otherwise. SQLite (the bootstrap-checks default) serializes
writers at the file level and raises `OperationalError: database table is
locked` under real thread contention, which isn't the thing under test.
"""
