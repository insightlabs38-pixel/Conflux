# Executive Freeze

## Frozen product model

An event is a staged competition workflow. Participants move through a Stage DAG; executable Policies and Temporal Gates govern actions; versioned Forms and typed Artifacts collect evidence; durable Projects accumulate identity while stage-specific Submissions freeze evidence; EvaluationPlans assign and aggregate judging; Awards consume results; Presentation composes the public site; all mutations flow through one application/API boundary with audit/outbox evidence.

## Frozen architecture

- Django 5.2 LTS + DRF modular monolith.
- PostgreSQL is authoritative state.
- React + TypeScript + Vite frontend.
- Valkey is disposable cache/broker state only.
- Celery for asynchronous jobs.
- Generic S3-compatible object-storage adapter; RustFS is the primary offline object store in Compose. SeaweedFS is the required compatibility target; ZeroS3 is optional and noncritical.
- Caddy reverse proxy.
- REST `/api/v1` application boundary; frontend uses the same domain/application path as external clients.
- Transactional outbox + readable AuditEvent log.
- Stable public IDs; normal relational DB keys remain internal.

## Frozen domain boundaries

Keep distinct:

- Workspace / Event
- identity / membership / role assignment
- Stage / StageEntry
- Project / Submission / SubmissionVersion
- Policy / TemporalGate / ExceptionGrant
- FormDefinition / immutable FormVersion / responses
- Artifact / upload intent / validators
- EvaluationPlan / assignment / ballot / aggregation
- Award / PrizePackage / fulfillment
- Theme / Page / PageBlock

## Scope strategy

1. T1–T4 are mandatory Core milestones.
2. Core continues beyond T4 to include multi-stage workflow, policies, typed evidence, normalization-aware judging, event templates, preflight, operations, portability, launch checks, upgrade/backup discipline, and polished builders.
3. Normalization Proof, API First, and Threat Model are natural Core outputs. Pairwise is Stretch #1 because bonuses are tie-breakers rather than score additions.
4. Stretch can be promoted whenever Core gates are green and integration/review capacity is healthy.
5. Very Stretch is intentionally large but contains only features with material organizer/participant/judge/adoption value.

## Red lines

Do not add generic BPM/workflow infrastructure, event sourcing, microservices/Kafka, arbitrary organizer code/JS/SQL, AI judging, blockchain/provenance theater, fake confidence scores, payment/KYC/tax, source-control hosting, or an Internet plugin marketplace.
