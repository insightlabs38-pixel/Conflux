# System Architecture

## Style

A modular monolith is the deployment and transaction boundary. Domain modules are separated by explicit services/contracts, not by network calls.

## Request/mutation path

`UI or external client → REST endpoint/application command → authentication/authorization → policy/gate evaluation → transaction → domain mutation + AuditEvent + DomainEvent(outbox) → commit → async side effects`.

No email, webhook call, Git provider request, remote validation or large object transfer may occur inside deadline-sensitive DB transactions.

## Runtime topology

`Caddy → Django/ASGI + built React assets`, with PostgreSQL, Valkey, Celery worker and local S3-compatible storage in the same offline Compose stack.

## Source of truth

- PostgreSQL: all authoritative business state.
- object store: artifact bytes referenced by authoritative DB metadata.
- Valkey: disposable cache/rate-limit/broker data only.
- outbox: durable async intent until delivery.

## Extensibility

Use code-level strategy/registry interfaces rather than generic runtime plugins:
- PolicyFactProvider / safe PolicyOperator
- StageTemplate / AdvancementStrategy
- FormFieldType
- ArtifactType / ArtifactValidator
- AssignmentStrategy / BallotStrategy / AggregationStrategy
- AwardSelectionStrategy / PrizeComponentType
- PageBlockType
- NotificationChannel
- Importer / Exporter
- RecordSigner

Adding Stretch should normally mean registering a new strategy/type/UI schema, not altering foundational tables.

## Public rendering acceptance

At least the gallery first page is returned with fixture title text present in raw HTML so the stdlib checker can verify it without JavaScript. React may hydrate/enhance the page afterward.

## No event sourcing

Audit and outbox records are evidence/integration infrastructure, not the source of truth. Current relational state remains canonical.
