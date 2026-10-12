# API, Webhooks and Portability

## API First
Versioned `/api/v1`. OpenAPI generated from real endpoints/schemas. UI uses the same application/domain path; do not maintain hidden UI-only business behavior.

## Credentials/scopes
Human sessions for UI plus explicit scoped API credentials/service tokens where needed. Event/workspace scope is always server-enforced.

## Webhooks
Outbox-driven delivery after commit; signatures; bounded retries/backoff; delivery history; replay/dead-letter recovery. Version the event envelope/schema.

## Canonical archive
A versioned import/export format carries event configuration and, depending on export mode, operational/event records. Include `format_version` and platform metadata. Import validates references and reports migrations rather than silently discarding unknown data.

## Migration path
Core includes full export/import roundtrip, compatibility tests and upgrade docs. Stretch adds source-specific migration adapters. Very Stretch adds migration preview/diff and signed archive manifests.

## Embed
Small dependency-light gallery Web Component consuming the public API; no external hosted dependency.
