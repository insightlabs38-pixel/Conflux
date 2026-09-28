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

## Authentication and sessions

Built-in username/password authentication is always available and is all the
offline stack needs. Sign-in creates a database-backed `Session` addressed by
an opaque, HttpOnly cookie; only a keyed digest of the token is stored (see
[SECURITY.md](SECURITY.md)). OpenID Connect is optional and additive
([SSO](docs/operations/SSO.md)); a provider identity never grants a role.

## Public list bounds

Public list endpoints are bounded. The gallery JSON endpoints
(`/api/v1/gallery/`, `/api/v1/events/{event}/gallery/`) keep their bare-array
bodies and take `limit` (1-100, default 50) and `offset`; totals and
navigation ride in `X-Total-Count` and `Link` (`rel="next"`/`"prev"`) headers,
and invalid values are a 400. Ordering is stable (`name`, then `public_id`).
The server-rendered gallery pages 24 projects at a time with `?page=` and keeps
the search/stage/track filters; the embeddable `<conflux-gallery>` loads further
pages on demand.

## Human-facing workflows

The role workspaces (participant, judge, organizer, plus a small mentor and
volunteer desk) expose the human PVS workflows; see
[PVS in the UI](docs/operations/PVS_UI.md) for the map and for what remains
API/CLI-first.
