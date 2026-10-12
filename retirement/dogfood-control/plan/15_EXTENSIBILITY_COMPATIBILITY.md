# Extensibility and Long-Term Compatibility

## Goal
Advanced features must be additions, not architecture rewrites.

## Registry boundaries
- `PolicyFactProvider`, bounded `PolicyOperator`
- `StageTemplate`, `AdvancementStrategy`
- `FormFieldType`
- `ArtifactType`, `ArtifactValidator`
- `AssignmentStrategy`, `BallotStrategy`, `AggregationStrategy`
- `AwardSelectionStrategy`, `PrizeComponentType`
- `PageBlockType`
- `NotificationChannel`
- `Importer`, `Exporter`
- `RecordSigner`

Registries are code-level interfaces with explicit schemas; this is not a dynamic Internet plugin marketplace.

## Versioning
- stable public IDs
- `/api/v1`
- webhook envelope/event schema versions
- immutable Form/Rubric/Policy versions where appropriate
- canonical archive `format_version`
- normal Django migrations
- migration smoke/upgrade tests

## Compatibility policy
Old templates/forms/policies/archives should either load unchanged or have an explicit migration path. Never silently reinterpret persisted rules.

## Future contributor ergonomics
Very Stretch may expose an internal extension SDK/reference examples, but Core should already have clean strategy interfaces and architecture docs.
