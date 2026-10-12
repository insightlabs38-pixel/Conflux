# Data Model Blueprint

## Organization and identity
`User`, `Workspace`, `WorkspaceMembership`, `Event`, `EventMembership`, `RoleAssignment`.

## Participation
`Team`, `TeamMembership`, `JudgePool`, `JudgePoolMembership`.

## Workflow
`Stage`, `StageTransition`, `StageEntry`, `AdvancementDecision`.

## Rules/time
`Policy`, immutable `PolicyVersion`, `PolicyBinding`, `TemporalGate`, `ExceptionGrant`, optional `PolicyEvaluationEvidence` for explainability without persisting every read.

## Forms/evidence
`FormDefinition`, `FormVersion`, `FormField`, `FormResponse`, `FormAnswer`; `Artifact`, `ArtifactUploadIntent`, `ArtifactValidation`.

## Projects/submissions
`Project`, `ProjectMembership`, `Submission`, immutable `SubmissionVersion`, `SubmissionArtifact`, `ModerationDecision`, `PreflightResult`.

## Evaluation
`EvaluationPlan`, `EvaluationCandidate`, `JudgeAssignment`, `Criterion`, `RubricVersion`, `Ballot`, `BallotResponse`, `EvaluationResult`, `ConflictOfInterest`, `NormalizationRun`, `NormalizationEffect`.

## Community
`CommunityBallot`, `CommunityVote`, `ProjectComment`, `AbuseSignal`, `RateLimit/Audit evidence` as appropriate.

## Awards
`Award`, `PrizePackage`, `PrizeComponent`, `AwardWinner`, `PrizeFulfillment`.

## Presentation
`Theme`, `Page`, `PageBlock`, `PresentationAsset`.

## Operational/integration
`AuditEvent`, `DomainEvent/OutboxRecord`, `WebhookSubscription`, `WebhookDelivery`, `IdempotencyRecord`, `ApiCredential`, `ImportExportJob`, `EventTemplate`.

## Core invariants
- event-scoped uniqueness/authorization constraints live in DB where feasible;
- a judge cannot query another judge's private ballot/score through any API path;
- finalized SubmissionVersion rows are immutable;
- policy/gate authorization is evaluated server-side;
- imported fixture duplicates remain distinct authoritative records and may be flagged separately;
- cache state never determines correctness;
- public API identity uses stable public IDs rather than implementation PKs.
