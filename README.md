# Conflux

Conflux runs staged competitions from event setup and submissions through
judging, awards, and a public gallery. The offline Compose stack includes
Django, a React client, PostgreSQL, Valkey, RustFS, and Caddy.

## Run locally

Install Docker with Compose, then run:

```sh
cp .env.example .env
# Set unique secrets and database/object-store passwords in .env.
make up
```

Open `http://localhost:8080` (or the `CONFLUX_PORT` in `.env`). Check
`http://localhost:8080/api/v1/health/` if startup is still in progress.
Compose builds the app image and applies database migrations at startup;
`make down` stops the stack without deleting its volumes. See
[upgrade and backup instructions](docs/operations/UPGRADES.md) before changing
an installation with real data.

Create an operator with `docker compose exec app python manage.py
createsuperuser`, then use `POST /api/v1/accounts/login/` with its username
and password to obtain a session cookie. Authenticated users can create a
workspace with `POST /api/v1/workspaces/`; the creator becomes its organizer.
The [API guide](docs/api/README.md) and [OpenAPI schema](docs/api/openapi.yaml)
cover the remaining routes. The browser workspace UI currently expects an
existing session and does not include a sign-in form; API login is required
before using its private pages.

For a disposable acceptance fixture, `make seed` imports the official data
and deterministic test identities. Use it only in a test installation.
[Acceptance evidence](acceptance-report.txt) records the exact released
checker result. The checker covers T1/T2; internal tests cover the remaining
Core behavior.

## Development

Requirements: Python 3.12, uv 0.12, Node 24, pnpm 12.

```sh
uv sync --frozen
pnpm install --frozen-lockfile
make verify-fast
```

`make verify` is the full local release check. `make format`, `make lint`,
`make test`, and `make build` expose the individual checks. The API entry
point is `src/api/manage.py`; the web app is `src/web`.
Non-Compose local checks use an isolated SQLite database; `DATABASE_URL` (set
by Compose) switches to PostgreSQL. Running the API directly requires
`DJANGO_SECRET_KEY` in the environment; the Makefile supplies a disposable
value for local checks only.

### Stack commands

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
