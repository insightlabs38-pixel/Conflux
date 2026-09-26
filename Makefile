.PHONY: format format-check lint test build verify-fast verify up dev dev-build down dev-down logs seed cold-boot-smoke

# Local checks use a disposable key; runtime deployments must supply their own.
export DJANGO_SECRET_KEY ?= bootstrap-checks-only

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
	uv run --frozen pytest
	pnpm test

build:
	uv run --frozen python src/api/manage.py check
	pnpm build

verify-fast: format-check lint test build

verify: verify-fast

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
	docker compose exec app python manage.py seed_acceptance_identities

# Proves the built images boot and serve with zero external dependency:
# reuses existing images and runs the compose network with no egress.
# Build first with `make up` if images don't exist yet.
cold-boot-smoke:
	./scripts/cold-offline-smoke
