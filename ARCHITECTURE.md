# Architecture

The frozen architecture is a Django 5.2/DRF modular monolith with a React,
TypeScript, and Vite frontend. PostgreSQL is authoritative; Valkey is
disposable cache and broker state; Celery runs asynchronous jobs. A generic
S3 adapter uses RustFS by default and must also pass SeaweedFS compatibility
tests. Caddy fronts the deployed API and built frontend. Domain mutations will
share one REST/application boundary, transactional outbox, and readable audit.
