# Architecture

Conflux is a Django 5.2/DRF modular monolith with a React, TypeScript, and Vite
frontend. PostgreSQL holds authoritative records; Valkey holds disposable
broker state for Celery. RustFS stores artifacts through the S3 adapter, with
SeaweedFS compatibility coverage. Caddy serves the API, public pages, static
files, and built frontend in the Compose stack.

Domain mutations use versioned REST routes, transaction-backed audit records,
and an outbox for asynchronous delivery. See the
[canonical archive](docs/architecture/CANONICAL_ARCHIVE.md),
[artifact serving](docs/architecture/ARTIFACT_SERVING.md), and
[upgrade discipline](docs/operations/UPGRADES.md) for data boundaries.
