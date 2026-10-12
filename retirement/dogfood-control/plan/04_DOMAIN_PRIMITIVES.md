# Fundamental Domain Primitives

## Workspace + Event
Workspace is the long-lived operator boundary; Event is the competition instance.

## Identity + Membership
User identity is global. WorkspaceMembership, EventMembership, RoleAssignment, TeamMembership and JudgePoolMembership are scoped relations. Roles are many-to-many and server-enforced.

## Stage Graph
Stage is a workflow/progression boundary. Stage type is a template/UI hint, not behavior. StageTransition forms an acyclic graph supporting branch/merge.

## StageEntry + Project + Submission
StageEntry says who/what participates at a stage. Project is durable identity. Submission is stage/evaluation evidence; SubmissionVersion freezes immutable evidence at finalization.

## Policy + Temporal Gate
Policies are safe typed data/AST, never arbitrary code. PolicyBinding attaches them to actions. TemporalGate owns schedule windows. ExceptionGrant is narrow/scoped/audited.

## Form + Artifact
FormDefinition has immutable published FormVersions. Fields support type, visibility and conditions. Artifacts are first-class typed evidence with validators.

## EvaluationPlan
Defines candidates, evaluator pool, assignment strategy, ballot strategy, aggregation strategy, visibility and completion. Multiple plans may coexist on one stage.

## Award + Prize
Awards consume eligibility/evaluation/manual sources; PrizePackages contain typed components and fulfillment state.

## Presentation
Theme + Page + PageBlock + PresentationAsset provide safe event branding without arbitrary organizer JS.

## Command/Event/API spine
All UI/external mutations use the same application command/service path. AuditEvent and relevant DomainEvent are committed transactionally.
