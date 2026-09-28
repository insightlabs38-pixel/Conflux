.PHONY: format format-check lint test build verify-fast verify openapi-check sdk-generate sdk-check up dev dev-build down dev-down logs seed cold-boot-smoke acceptance backup restore backup-restore-smoke

# Local checks use disposable keys; runtime deployments must supply their own.
export DJANGO_SECRET_KEY ?= bootstrap-checks-only
export RECORD_SIGNING_KEY_SEED ?= bootstrap-checks-only-record-signing-seed

format:
	uv run ruff format src/api tests
	uv run ruff check --fix src/api tests
	pnpm format

format-check:
	uv run --frozen ruff format --check src/api tests
	pnpm format:check

lint:
	uv run --frozen ruff check src/api tests
	pnpm lint

test:
	uv run --frozen pytest -n auto
	pnpm test

build:
	uv run --frozen python src/api/manage.py check
	pnpm build

verify-fast: format-check lint test build sdk-check block-schema-check

verify: verify-fast

openapi-check:
	uv run --frozen python scripts/check_openapi_artifact.py

.PHONY: block-schema-generate block-schema-check
block-schema-generate:
	uv run --frozen python scripts/generate_block_schemas.py

block-schema-check:
	uv run --frozen python scripts/generate_block_schemas.py --check

sdk-generate:
	uv run --frozen python scripts/generate_sdks.py

sdk-check: openapi-check
	uv run --frozen python scripts/generate_sdks.py --check
	pnpm --filter @conflux/sdk build

# Translation catalogs (VS23): compiles locale/<lang>/LC_MESSAGES/django.po
# to .mo via Django's own management command (shells out to msgfmt).
# `make messages` re-extracts msgids from templates into the .po (merges,
# never discards existing translations) after adding/changing a
# {% trans %}/{% blocktrans %} string.
messages:
	cd src/api && uv run --frozen python manage.py makemessages -l es

compile-messages:
	cd src/api && uv run --frozen python manage.py compilemessages

i18n-check:
	@tmp=$$(mktemp) && \
	msgfmt src/api/locale/es/LC_MESSAGES/django.po -o "$$tmp" && \
	cmp "$$tmp" src/api/locale/es/LC_MESSAGES/django.mo && \
	rm "$$tmp"

# Authoritative clean/offline build+boot — full image rebuild every time.
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

# Fast iteration: source is bind-mounted, Django reloads in place, and the
# frontend runs through Vite's dev server (HMR). Only rebuilds the image if
# none exists yet; run `make dev-build` after a Dockerfile/dependency change.
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

dev-build:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

seed:
	docker compose exec app python manage.py import_fixture fixtures/fixtures.json
	docker compose exec app python manage.py seed_acceptance_identities
	docker compose exec app python manage.py link_judge_identities

# Proves the built images boot and serve with zero external dependency:
# reuses existing images and runs the compose network with no egress.
# Build first with `make up` if images don't exist yet.
cold-boot-smoke:
	./scripts/cold-offline-smoke

# Regenerates acceptance-report.txt from the exact official checker against
# the running stack (`make up` first).
acceptance:
	./scripts/run-acceptance

# Back up the running stack's authoritative state (Postgres + the object
# store volume) to backups/<timestamp>/, or DEST if given.
backup:
	./scripts/backup $(DEST)

# Restore a backup produced by `make backup` (DEST=path required).
restore:
	./scripts/restore $(DEST)

# Proves backup+restore actually round-trip real state end to end.
backup-restore-smoke:
	./scripts/backup-restore-smoke
