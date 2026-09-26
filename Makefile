.PHONY: format format-check lint test build verify-fast verify

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
