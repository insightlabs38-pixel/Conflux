# API v1 conventions

All application API routes live under `/api/v1/`. JSON routes end in `/`; CSV export routes end in `.csv`. IDs in paths and resource responses are stable public UUIDs. Nested event routes include the workspace ID and enforce workspace and event ownership on the server. Public routes use an explicit `public/` prefix or a documented public event route.

Requests and responses use JSON except documented exports and uploads. Timestamps are ISO 8601 values with timezone information. Successful creates return HTTP 201, permission failures return 401 or 403, missing scoped resources return 404, and invalid input returns 400 with a JSON error body. Existing organizer configuration GET routes may lazily create a default record; clients should treat those responses as stateful.

Human UI requests use the `session` cookie. Service credentials and their explicit scopes are introduced by API-003. The generated schema and its self-check are introduced by API-004; this document defines the route and representation rules used by both.
