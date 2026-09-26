# Conflux

Conflux is a staged competition platform, built up incrementally by Core
tasks. The offline runtime (PostgreSQL, Valkey, RustFS, Caddy) is composed in
`docker-compose.yml`.

## Development

Requirements: Python 3.12, uv 0.12, Node 24, pnpm 12.

```sh
uv sync --frozen
pnpm install --frozen-lockfile
make verify-fast
```

`make format`, `make lint`, `make test`, and `make build` expose the individual
checks. The API entry point is `src/api/manage.py`; the web app is `src/web`.
Non-Compose local checks use an isolated SQLite database; `DATABASE_URL` (set
by Compose) switches to PostgreSQL. Running the API directly requires
`DJANGO_SECRET_KEY` in the environment; the Makefile supplies a disposable
value for local checks only.

### Running the stack

```sh
make up      # clean, offline build — full image rebuild, authoritative
make dev     # fast iteration — bind-mounted source, Django auto-reloads,
             #   frontend via Vite dev server/HMR (http://localhost:5173)
make logs
make down    # or `make dev-down` for the dev overlay
make seed    # deterministic acceptance identities
```

Use `make dev` for day-to-day edits: it only rebuilds the image if one doesn't
exist yet. Run `make dev-build` after changing a Dockerfile or a
dependency/lockfile. `make up` always rebuilds and remains the authoritative
clean-build path for release verification.
