# Technology Stack and Offline Runtime

## Frontend
React, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod, Radix/headless source-owned components, Tailwind/CSS custom properties.

## Backend
Python, Django 5.2 LTS, Django REST Framework, drf-spectacular/OpenAPI, Uvicorn/ASGI, psycopg3 pooling.

## Data/async
PostgreSQL; Valkey for disposable cache/broker; Celery workers; transactional outbox.

## Object storage
A generic S3 adapter. The offline default uses a locally hosted S3-compatible service. Presigned/direct browser uploads avoid routing large bytes through Django.

## Proxy
Caddy provides one local origin and serves/proxies API + built frontend.

## Testing
pytest/pytest-django, Playwright, property/fuzz tooling appropriate to Python/TS, and k6 or Locust for load generation. High-volume fuzzing/property/permutation work is primarily a Freebuff verification responsibility.

## Offline invariant
`docker compose up` must yield a fully functional seeded portal with the network disconnected. No hosted authentication, hosted DB, external API, cloud object store or proprietary tool is required.
