# Conflux

Conflux is a staged competition platform. This repository currently contains
the BOOT-B00 framework baseline; product workflows and the offline runtime are
implemented by subsequent Core tasks.

## Development

Requirements: Python 3.12, uv 0.12, Node 24, pnpm 12.

```sh
uv sync --frozen
pnpm install --frozen-lockfile
make verify-fast
```

`make format`, `make lint`, `make test`, and `make build` expose the individual
checks. The API entry point is `src/api/manage.py`; the web app is `src/web`.
The bootstrap settings use an isolated SQLite database for local checks. The
planned PostgreSQL, Valkey, Celery, RustFS, and Caddy runtime is built in later
Core tasks. Running the API directly requires `DJANGO_SECRET_KEY` in the
environment; the Makefile supplies a disposable value for local checks only.
