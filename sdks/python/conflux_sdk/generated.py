"""Generated from docs/api/openapi.yaml. Run scripts/generate_sdks.py."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

class AbuseSignalSchema(TypedDict):
    public_id: str
    signal_type: str
    detail: str
    evidence: Any
    occurred_at: str
    resolved_at: str | None
    resolved_by: str | None
    resolution_note: str

class InputOfAbuseSignalSchema(TypedDict):
    public_id: str
    signal_type: str
    detail: str
    evidence: Any
    occurred_at: str
    resolved_at: str | None
    resolved_by: str | None
    resolution_note: str

AccessEnum = Literal['roles', 'any_authenticated', 'public', 'unknown']

InputOfAccessEnum = Literal['roles', 'any_authenticated', 'public', 'unknown']

class AccessibilityWarning(TypedDict):
    category: CategoryEnum
    severity: str
    message: str
    block_public_id: str | None

class InputOfAccessibilityWarning(TypedDict):
    category: InputOfCategoryEnum
    severity: str
    message: str
    block_public_id: str | None

ActionEnum = Literal['submit', 'join', 'advance', 'vote', 'award']

InputOfActionEnum = Literal['submit', 'join', 'advance', 'vote', 'award']

class AddProjectMemberInput(TypedDict):
    user: str

class InputOfAddProjectMemberInput(TypedDict):
    user: str

class AdvancedSubjectSchema(TypedDict):
    subject_type: str
    subject_id: str

class InputOfAdvancedSubjectSchema(TypedDict):
    subject_type: str
    subject_id: str

class AdvancementCandidateSchema(TypedDict):
    subject_type: str
    subject_id: str
    score: NotRequired[float | None]
    track_id: NotRequired[str | None]

class InputOfAdvancementCandidateSchema(TypedDict):
    subject_type: str
    subject_id: str
    score: NotRequired[float | None]
    track_id: NotRequired[str | None]

class AdvancementEvidenceSchema(TypedDict):
    created_at: str
    actor: str | None
    stage_public_id: str
    metadata: Any

class InputOfAdvancementEvidenceSchema(TypedDict):
    created_at: str
    actor: str | None
    stage_public_id: str
    metadata: Any

class AdvancementInputSchema(TypedDict):
    to_stage: str
    strategy: str
    params: NotRequired[Any]
    candidates: list[AdvancementCandidateSchema]

class InputOfAdvancementInputSchema(TypedDict):
    to_stage: str
    strategy: str
    params: NotRequired[Any]
    candidates: list[InputOfAdvancementCandidateSchema]

class AdvancementResultSchema(TypedDict):
    advanced: list[AdvancedSubjectSchema]

class InputOfAdvancementResultSchema(TypedDict):
    advanced: list[InputOfAdvancedSubjectSchema]

class AdvancementStrategiesSchema(TypedDict):
    strategies: list[str]

class InputOfAdvancementStrategiesSchema(TypedDict):
    strategies: list[str]

class AgreementCriterionSchema(TypedDict):
    project: str
    project_name: str
    criterion_id: str
    scores: dict[str, float]
    mean: float
    range: float
    stdev: float

class InputOfAgreementCriterionSchema(TypedDict):
    project: str
    project_name: str
    criterion_id: str
    scores: dict[str, float]
    mean: float
    range: float
    stdev: float

class AgreementRankingSchema(TypedDict):
    judge_a: str
    judge_b: str
    shared_candidates: int
    tau: float | None

class InputOfAgreementRankingSchema(TypedDict):
    judge_a: str
    judge_b: str
    shared_candidates: int
    tau: float | None

class AgreementSummarySchema(TypedDict):
    criteria: list[AgreementCriterionSchema]
    rankings: list[AgreementRankingSchema]

class InputOfAgreementSummarySchema(TypedDict):
    criteria: list[InputOfAgreementCriterionSchema]
    rankings: list[InputOfAgreementRankingSchema]

class Announcement(TypedDict):
    public_id: str
    title: str
    body: NotRequired[str]
    posted_by: str
    created_at: str
    hidden_at: str | None
    version: int

class InputOfAnnouncement(TypedDict):
    title: str
    body: NotRequired[str]

class AnnouncementReviewInput(TypedDict):
    version: int
    status: AnnouncementReviewInputStatusEnum
    note: str

class InputOfAnnouncementReviewInput(TypedDict):
    version: int
    status: InputOfAnnouncementReviewInputStatusEnum
    note: str

AnnouncementReviewInputStatusEnum = Literal['published', 'hidden']

InputOfAnnouncementReviewInputStatusEnum = Literal['published', 'hidden']

class AnnouncementReviewOutput(TypedDict):
    public_id: str
    title: str
    body: str
    created_at: str
    version: int
    hidden_at: str | None

class InputOfAnnouncementReviewOutput(TypedDict):
    pass

class AppealDecisionInputSchema(TypedDict):
    status: AppealDecisionInputSchemaStatusEnum
    decision_note: NotRequired[str]

class InputOfAppealDecisionInputSchema(TypedDict):
    status: InputOfAppealDecisionInputSchemaStatusEnum
    decision_note: NotRequired[str]

AppealDecisionInputSchemaStatusEnum = Literal['upheld', 'overturned', 'dismissed']

InputOfAppealDecisionInputSchemaStatusEnum = Literal['upheld', 'overturned', 'dismissed']

class AppealInputSchema(TypedDict):
    project: str
    body: str

class InputOfAppealInputSchema(TypedDict):
    project: str
    body: str

class AppealSchema(TypedDict):
    public_id: str
    project: str
    project_name: str
    submitted_by: str
    submitted_by_username: str
    body: str
    status: str
    decision_note: str
    decided_by: str | None
    decided_at: str | None
    created_at: str

class InputOfAppealSchema(TypedDict):
    public_id: str
    project: str
    project_name: str
    submitted_by: str
    submitted_by_username: str
    body: str
    status: str
    decision_note: str
    decided_by: str | None
    decided_at: str | None
    created_at: str

class ApplicationDecisionInputSchema(TypedDict):
    decision: ApplicationDecisionInputSchemaDecisionEnum

class InputOfApplicationDecisionInputSchema(TypedDict):
    decision: InputOfApplicationDecisionInputSchemaDecisionEnum

ApplicationDecisionInputSchemaDecisionEnum = Literal['approved', 'waitlisted', 'rejected']

InputOfApplicationDecisionInputSchemaDecisionEnum = Literal['approved', 'waitlisted', 'rejected']

class ApplyInput(TypedDict):
    apply: NotRequired[bool]
    kind: NotRequired[ApplyInputKindEnum]

class InputOfApplyInput(TypedDict):
    apply: NotRequired[bool]
    kind: NotRequired[InputOfApplyInputKindEnum]

ApplyInputKindEnum = Literal['table', 'booth']

InputOfApplyInputKindEnum = Literal['table', 'booth']

class ApplyToEventInputSchema(TypedDict):
    note: NotRequired[str]
    code: NotRequired[str]

class InputOfApplyToEventInputSchema(TypedDict):
    note: NotRequired[str]
    code: NotRequired[str]

class ArchiveImportInput(TypedDict):
    name: str
    slug: str
    archive: Any

class InputOfArchiveImportInput(TypedDict):
    name: str
    slug: str
    archive: Any

class ArchiveOutput(TypedDict):
    format_version: int
    mode: str
    event: dict[str, Any]
    tracks: NotRequired[list[dict[str, Any]]]
    base_prizes: NotRequired[list[dict[str, Any]]]
    stages: NotRequired[list[dict[str, Any]]]
    stage_transitions: NotRequired[list[dict[str, Any]]]
    forms: NotRequired[list[dict[str, Any]]]
    policies: NotRequired[list[dict[str, Any]]]
    temporal_gates: NotRequired[list[dict[str, Any]]]
    policy_bindings: NotRequired[list[dict[str, Any]]]
    awards: NotRequired[list[dict[str, Any]]]
    projects: NotRequired[list[dict[str, Any]]]
    evaluation_plans: NotRequired[list[dict[str, Any]]]
    pages: NotRequired[list[dict[str, Any]]]
    tables: NotRequired[dict[str, Any]]
    users: NotRequired[list[dict[str, Any]]]
    provenance: NotRequired[list[dict[str, Any]]]

class InputOfArchiveOutput(TypedDict):
    format_version: int
    mode: str
    event: dict[str, Any]
    tracks: NotRequired[list[dict[str, Any]]]
    base_prizes: NotRequired[list[dict[str, Any]]]
    stages: NotRequired[list[dict[str, Any]]]
    stage_transitions: NotRequired[list[dict[str, Any]]]
    forms: NotRequired[list[dict[str, Any]]]
    policies: NotRequired[list[dict[str, Any]]]
    temporal_gates: NotRequired[list[dict[str, Any]]]
    policy_bindings: NotRequired[list[dict[str, Any]]]
    awards: NotRequired[list[dict[str, Any]]]
    projects: NotRequired[list[dict[str, Any]]]
    evaluation_plans: NotRequired[list[dict[str, Any]]]
    pages: NotRequired[list[dict[str, Any]]]
    tables: NotRequired[dict[str, Any]]
    users: NotRequired[list[dict[str, Any]]]
    provenance: NotRequired[list[dict[str, Any]]]

class ArchivePreviewChange(TypedDict):
    field: str
    source: Any
    imported: Any

class InputOfArchivePreviewChange(TypedDict):
    field: str
    source: Any
    imported: Any

class ArchivePreviewOutput(TypedDict):
    format_version: int
    mode: str
    migration_steps: list[str]
    deprecations: list[str]
    event_changes: list[ArchivePreviewChange]
    sections: list[ArchivePreviewSection]
    ignored_sections: list[str]

class InputOfArchivePreviewOutput(TypedDict):
    format_version: int
    mode: str
    migration_steps: list[str]
    deprecations: list[str]
    event_changes: list[InputOfArchivePreviewChange]
    sections: list[InputOfArchivePreviewSection]
    ignored_sections: list[str]

class ArchivePreviewSection(TypedDict):
    section: str
    source_count: int
    imported_count: int

class InputOfArchivePreviewSection(TypedDict):
    section: str
    source_count: int
    imported_count: int

ArtifactKindEnum = Literal['file', 'image', 'video', 'external_video', 'repository', 'live_url', 'document', 'dataset', 'secret']

InputOfArtifactKindEnum = Literal['file', 'image', 'video', 'external_video', 'repository', 'live_url', 'document', 'dataset', 'secret']

class ArtifactSchema(TypedDict):
    public_id: str
    kind: str
    visibility: str
    title: str
    external_url: str
    content_type: str
    byte_size: int | None
    status: str
    validation: ValidationSchema | None
    ci_evidence: NotRequired[list[ValidationSchema]]
    download_url: NotRequired[str]

class InputOfArtifactSchema(TypedDict):
    public_id: str
    kind: str
    visibility: str
    title: str
    external_url: str
    content_type: str
    byte_size: int | None
    status: str
    validation: InputOfValidationSchema | None
    ci_evidence: NotRequired[list[InputOfValidationSchema]]
    download_url: NotRequired[str]

class Assignment(TypedDict):
    judge: str
    project: str

class InputOfAssignment(TypedDict):
    pass

class AssignmentActivateInputSchema(TypedDict):
    coverage: NotRequired[int]

class InputOfAssignmentActivateInputSchema(TypedDict):
    coverage: NotRequired[int]

class AssignmentCompareInputSchema(TypedDict):
    coverage: NotRequired[int]

class InputOfAssignmentCompareInputSchema(TypedDict):
    coverage: NotRequired[int]

class AssignmentCompareSchema(TypedDict):
    heuristic: AssignmentCoveragePreviewSchema
    optimized: AssignmentCoveragePreviewSchema

class InputOfAssignmentCompareSchema(TypedDict):
    heuristic: InputOfAssignmentCoveragePreviewSchema
    optimized: InputOfAssignmentCoveragePreviewSchema

class AssignmentCoveragePreviewSchema(TypedDict):
    solver: str
    coverage: int
    candidate_count: int
    judge_count: int
    assignment_count: int
    load_by_judge: dict[str, int]
    conflict_count: int
    connectivity: dict[str, Any]

class InputOfAssignmentCoveragePreviewSchema(TypedDict):
    solver: str
    coverage: int
    candidate_count: int
    judge_count: int
    assignment_count: int
    load_by_judge: dict[str, int]
    conflict_count: int
    connectivity: dict[str, Any]

class AssignmentInput(TypedDict):
    taxonomy: str
    subject: SubjectInput
    terms: list[str]

class InputOfAssignmentInput(TypedDict):
    taxonomy: str
    subject: InputOfSubjectInput
    terms: list[str]

class AssignmentOutput(TypedDict):
    taxonomy: str
    term: str
    subject: dict[str, Any]

class InputOfAssignmentOutput(TypedDict):
    taxonomy: str
    term: str
    subject: dict[str, Any]

class AssignmentPreviewInputSchema(TypedDict):
    coverage_options: NotRequired[list[int]]

class InputOfAssignmentPreviewInputSchema(TypedDict):
    coverage_options: NotRequired[list[int]]

class AssignmentRebalanceInputSchema(TypedDict):
    drop_judges: NotRequired[list[str]]
    coverage: NotRequired[int]

class InputOfAssignmentRebalanceInputSchema(TypedDict):
    drop_judges: NotRequired[list[str]]
    coverage: NotRequired[int]

class AssignmentVersion(TypedDict):
    public_id: str
    number: int
    coverage: int
    evidence: NotRequired[Any]
    assignments: list[Assignment]
    created_at: str

class InputOfAssignmentVersion(TypedDict):
    number: int
    coverage: int
    evidence: NotRequired[Any]

class AttemptOutput(TypedDict):
    public_id: str
    destination: str
    body: str
    headers: dict[str, str]
    started_at: str
    completed_at: str | None
    status_code: int | None
    error: str

class InputOfAttemptOutput(TypedDict):
    public_id: str
    destination: str
    body: str
    headers: dict[str, str]
    started_at: str
    completed_at: str | None
    status_code: int | None
    error: str

class AttendanceInput(TypedDict):
    mode: AttendanceInputModeEnum

class InputOfAttendanceInput(TypedDict):
    mode: InputOfAttendanceInputModeEnum

AttendanceInputModeEnum = Literal['in_person', 'remote', 'not_attending']

InputOfAttendanceInputModeEnum = Literal['in_person', 'remote', 'not_attending']

class AudienceKindSchema(TypedDict):
    key: str
    label: str
    param_names: list[str]
    options: Any

class InputOfAudienceKindSchema(TypedDict):
    key: str
    label: str
    param_names: list[str]
    options: Any

class AudienceMemberSchema(TypedDict):
    public_id: str
    username: str

class InputOfAudienceMemberSchema(TypedDict):
    public_id: str
    username: str

class AudiencePreviewInputSchema(TypedDict):
    audience_kind: str
    audience_params: NotRequired[Any]

class InputOfAudiencePreviewInputSchema(TypedDict):
    audience_kind: str
    audience_params: NotRequired[Any]

class AudiencePreviewSchema(TypedDict):
    count: int
    sample: list[AudienceMemberSchema]

class InputOfAudiencePreviewSchema(TypedDict):
    count: int
    sample: list[InputOfAudienceMemberSchema]

class AuditEventSchema(TypedDict):
    public_id: str
    actor: str | None
    action: str
    target_type: str
    target_id: str
    metadata: Any
    created_at: str

class InputOfAuditEventSchema(TypedDict):
    public_id: str
    actor: str | None
    action: str
    target_type: str
    target_id: str
    metadata: Any
    created_at: str

class AuthzDryRunInputSchema(TypedDict):
    path: str
    method: MethodEnum
    subject_kind: SubjectKindEnum
    subject: str

class InputOfAuthzDryRunInputSchema(TypedDict):
    path: str
    method: InputOfMethodEnum
    subject_kind: InputOfSubjectKindEnum
    subject: str

class AuthzDryRunOutputSchema(TypedDict):
    allowed: bool
    mode: AuthzDryRunOutputSchemaModeEnum
    access: NotRequired[str]
    roles: NotRequired[list[str]]
    actual_roles: NotRequired[list[str]]

class InputOfAuthzDryRunOutputSchema(TypedDict):
    allowed: bool
    mode: InputOfAuthzDryRunOutputSchemaModeEnum
    access: NotRequired[str]
    roles: NotRequired[list[str]]
    actual_roles: NotRequired[list[str]]

AuthzDryRunOutputSchemaModeEnum = Literal['live', 'hypothetical']

InputOfAuthzDryRunOutputSchemaModeEnum = Literal['live', 'hypothetical']

class AwardInput(TypedDict):
    name: str
    description: NotRequired[str]
    eligibility_track: NotRequired[str | None]
    require_finalized_submission: NotRequired[bool]
    selection_source: SelectionSourceEnum
    evaluation_plan: NotRequired[str | None]
    winner_count: int
    allow_stacking: NotRequired[bool]
    conflict_group: NotRequired[str]

class InputOfAwardInput(TypedDict):
    name: str
    description: NotRequired[str]
    eligibility_track: NotRequired[str | None]
    require_finalized_submission: NotRequired[bool]
    selection_source: InputOfSelectionSourceEnum
    evaluation_plan: NotRequired[str | None]
    winner_count: int
    allow_stacking: NotRequired[bool]
    conflict_group: NotRequired[str]

class AwardOutput(TypedDict):
    public_id: str
    name: str
    description: str
    eligibility_track: str | None
    require_finalized_submission: bool
    selection_source: str
    evaluation_plan: str | None
    winner_count: int
    allow_stacking: bool
    conflict_group: str
    published_at: str | None
    components: list[ComponentOutput]
    winners: list[WinnerOutput]
    sponsor_contacts: list[str]

class InputOfAwardOutput(TypedDict):
    public_id: str
    name: str
    description: str
    eligibility_track: str | None
    require_finalized_submission: bool
    selection_source: str
    evaluation_plan: str | None
    winner_count: int
    allow_stacking: bool
    conflict_group: str
    published_at: str | None
    components: list[InputOfComponentOutput]
    winners: list[InputOfWinnerOutput]
    sponsor_contacts: list[str]

class AwardProposalItem(TypedDict):
    award: str
    name: str
    existing: list[str]
    proposed: list[str]
    unfilled: int
    blocker: str | None

class InputOfAwardProposalItem(TypedDict):
    award: str
    name: str
    existing: list[str]
    proposed: list[str]
    unfilled: int
    blocker: str | None

class AwardProposalOutput(TypedDict):
    search_limited: bool
    awards: list[AwardProposalItem]

class InputOfAwardProposalOutput(TypedDict):
    search_limited: bool
    awards: list[InputOfAwardProposalItem]

class Ballot(TypedDict):
    public_id: str
    project: str
    comment: NotRequired[str]
    responses: list[BallotResponse]
    submitted_at: str

class InputOfBallot(TypedDict):
    comment: NotRequired[str]
    responses: list[InputOfBallotResponse]

class BallotDraft(TypedDict):
    public_id: str
    project: str
    responses: NotRequired[Any]
    comment: NotRequired[str]
    updated_at: str

class InputOfBallotDraft(TypedDict):
    responses: NotRequired[Any]
    comment: NotRequired[str]

class BallotDraftInputSchema(TypedDict):
    responses: NotRequired[Any]
    comment: NotRequired[str]

class InputOfBallotDraftInputSchema(TypedDict):
    responses: NotRequired[Any]
    comment: NotRequired[str]

class BallotResponse(TypedDict):
    criterion_id: str
    score: float

class InputOfBallotResponse(TypedDict):
    criterion_id: str
    score: float

class BallotSubmitInputSchema(TypedDict):
    project: str
    comment: NotRequired[str]
    responses: list[BallotResponse]

class InputOfBallotSubmitInputSchema(TypedDict):
    project: str
    comment: NotRequired[str]
    responses: list[InputOfBallotResponse]

class BasePrize(TypedDict):
    public_id: str
    name: str
    description: NotRequired[str]
    kind: BasePrizeKind
    amount: NotRequired[str | None]
    currency: NotRequired[str]
    track: NotRequired[str | None]
    position: NotRequired[int]

class InputOfBasePrize(TypedDict):
    name: str
    description: NotRequired[str]
    kind: InputOfBasePrizeKind
    amount: NotRequired[str | None]
    currency: NotRequired[str]
    track: NotRequired[str | None]
    position: NotRequired[int]

BasePrizeKind = Literal['cash', 'credit', 'discount', 'subscription', 'hardware', 'travel', 'service', 'mentorship', 'swag', 'other']

InputOfBasePrizeKind = Literal['cash', 'credit', 'discount', 'subscription', 'hardware', 'travel', 'service', 'mentorship', 'swag', 'other']

BulkOperationAction = Literal['assign', 'advance', 'extend', 'move', 'send']

InputOfBulkOperationAction = Literal['assign', 'advance', 'extend', 'move', 'send']

class BulkOperationInput(TypedDict):
    action: BulkOperationAction
    plan: NotRequired[str]
    coverage: NotRequired[int]
    stage: NotRequired[str]
    to_stage: NotRequired[str]
    entries: NotRequired[list[str]]
    gates: NotRequired[list[str]]
    seconds: NotRequired[int]
    projects: NotRequired[list[str]]
    track: NotRequired[str]
    subject: NotRequired[str]
    body: NotRequired[str]
    audience_kind: NotRequired[str]
    audience_params: NotRequired[dict[str, Any]]

class InputOfBulkOperationInput(TypedDict):
    action: InputOfBulkOperationAction
    plan: NotRequired[str]
    coverage: NotRequired[int]
    stage: NotRequired[str]
    to_stage: NotRequired[str]
    entries: NotRequired[list[str]]
    gates: NotRequired[list[str]]
    seconds: NotRequired[int]
    projects: NotRequired[list[str]]
    track: NotRequired[str]
    subject: NotRequired[str]
    body: NotRequired[str]
    audience_kind: NotRequired[str]
    audience_params: NotRequired[dict[str, Any]]

class BulkRequest(TypedDict):
    operations: list[BulkOperationInput]
    preview_token: NotRequired[str]

class InputOfBulkRequest(TypedDict):
    operations: list[InputOfBulkOperationInput]
    preview_token: NotRequired[str]

class BulkResponse(TypedDict):
    applied: bool
    effects: list[Any]
    preview_token: NotRequired[str]
    expires_in: NotRequired[int]

class InputOfBulkResponse(TypedDict):
    applied: bool
    effects: list[Any]
    preview_token: NotRequired[str]
    expires_in: NotRequired[int]

COIRelationshipKind = Literal['team', 'institution', 'domain']

InputOfCOIRelationshipKind = Literal['team', 'institution', 'domain']

class COIRuleInputSchema(TypedDict):
    kind: COIRuleKind
    enabled: bool

class InputOfCOIRuleInputSchema(TypedDict):
    kind: InputOfCOIRuleKind
    enabled: bool

COIRuleKind = Literal['team_membership', 'project_membership', 'project_creator']

InputOfCOIRuleKind = Literal['team_membership', 'project_membership', 'project_creator']

class COIRuleOutputSchema(TypedDict):
    kind: COIRuleKind
    enabled: bool

class InputOfCOIRuleOutputSchema(TypedDict):
    kind: InputOfCOIRuleKind
    enabled: bool

class CalendarAssignmentSchema(TypedDict):
    stage_name: str
    plan: str
    plan_name: str
    rubric_published: bool
    assigned_count: int
    submitted_count: int
    completion_ratio: float | None

class InputOfCalendarAssignmentSchema(TypedDict):
    stage_name: str
    plan: str
    plan_name: str
    rubric_published: bool
    assigned_count: int
    submitted_count: int
    completion_ratio: float | None

class CalendarWindowSchema(TypedDict):
    name: str
    opens_at: str | None
    closes_at: str | None
    status: CalendarWindowSchemaStatusEnum

class InputOfCalendarWindowSchema(TypedDict):
    name: str
    opens_at: str | None
    closes_at: str | None
    status: InputOfCalendarWindowSchemaStatusEnum

CalendarWindowSchemaStatusEnum = Literal['not_yet_open', 'open', 'closed']

InputOfCalendarWindowSchemaStatusEnum = Literal['not_yet_open', 'open', 'closed']

class CalibrationCriterionSummarySchema(TypedDict):
    criterion_id: str
    scores: dict[str, float]
    min: float
    max: float
    mean: float
    spread: float

class InputOfCalibrationCriterionSummarySchema(TypedDict):
    criterion_id: str
    scores: dict[str, float]
    min: float
    max: float
    mean: float
    spread: float

class CalibrationOverviewSchema(TypedDict):
    required: bool
    project_count: int
    judges_total: int
    judges_complete: int

class InputOfCalibrationOverviewSchema(TypedDict):
    required: bool
    project_count: int
    judges_total: int
    judges_complete: int

class CalibrationProjectItemSchema(TypedDict):
    project: str
    name: str

class InputOfCalibrationProjectItemSchema(TypedDict):
    project: str
    name: str

class CalibrationProjectSummarySchema(TypedDict):
    project: str
    project_name: str
    criteria: list[CalibrationCriterionSummarySchema]

class InputOfCalibrationProjectSummarySchema(TypedDict):
    project: str
    project_name: str
    criteria: list[InputOfCalibrationCriterionSummarySchema]

class CalibrationProjectsInputSchema(TypedDict):
    projects: list[str]

class InputOfCalibrationProjectsInputSchema(TypedDict):
    projects: list[str]

class CalibrationStatusSchema(TypedDict):
    required: bool
    total: int
    completed: list[str]
    remaining: list[str]
    is_complete: bool

class InputOfCalibrationStatusSchema(TypedDict):
    required: bool
    total: int
    completed: list[str]
    remaining: list[str]
    is_complete: bool

class CandidateOutput(TypedDict):
    public_id: str
    name: str
    track: str | None
    has_finalized_submission: bool

class InputOfCandidateOutput(TypedDict):
    public_id: str
    name: str
    track: str | None
    has_finalized_submission: bool

class CandidateQueueItemSchema(TypedDict):
    project: str
    name: str
    status: CandidateQueueStatus

class InputOfCandidateQueueItemSchema(TypedDict):
    project: str
    name: str
    status: InputOfCandidateQueueStatus

CandidateQueueStatus = Literal['pending', 'drafted', 'submitted']

InputOfCandidateQueueStatus = Literal['pending', 'drafted', 'submitted']

class CandidateSchema(TypedDict):
    project: str
    name: str

class InputOfCandidateSchema(TypedDict):
    project: str
    name: str

CandidateTypeEnum = Literal['project']

InputOfCandidateTypeEnum = Literal['project']

CategoryEnum = Literal['contrast', 'heading', 'accessible-name', 'keyboard']

InputOfCategoryEnum = Literal['contrast', 'heading', 'accessible-name', 'keyboard']

class CheckIn(TypedDict):
    public_id: str
    participant: str
    participant_username: str
    checked_in_by: str
    checked_in_at: str

class InputOfCheckIn(TypedDict):
    pass

class CheckInInputSchema(TypedDict):
    participant: str

class InputOfCheckInInputSchema(TypedDict):
    participant: str

class ChecklistItemSchema(TypedDict):
    id: str
    severity: str
    passed: bool
    detail: str

class InputOfChecklistItemSchema(TypedDict):
    id: str
    severity: str
    passed: bool
    detail: str

class CloneInput(TypedDict):
    name: str
    slug: str
    sections: NotRequired[list[str]]

class InputOfCloneInput(TypedDict):
    name: str
    slug: str
    sections: NotRequired[list[str]]

class CloseCallsSchema(TypedDict):
    normalization_run: int | None
    projects: list[str]

class InputOfCloseCallsSchema(TypedDict):
    normalization_run: int | None
    projects: list[str]

class CloseInput(TypedDict):
    state: CloseInputStateEnum
    note: NotRequired[str]

class InputOfCloseInput(TypedDict):
    state: InputOfCloseInputStateEnum
    note: NotRequired[str]

CloseInputStateEnum = Literal['resolved', 'waived']

InputOfCloseInputStateEnum = Literal['resolved', 'waived']

class Comment(TypedDict):
    public_id: str
    author: str
    body: str
    created_at: str
    hidden_at: str | None

class InputOfComment(TypedDict):
    body: str

CommentVisibilityEnum = Literal['organizer', 'organizer_judge', 'everyone']

InputOfCommentVisibilityEnum = Literal['organizer', 'organizer_judge', 'everyone']

class CommunityAuditSchema(TypedDict):
    public_id: str
    actor: str | None
    action: str
    detail: str
    created_at: str

class InputOfCommunityAuditSchema(TypedDict):
    public_id: str
    actor: str | None
    action: str
    detail: str
    created_at: str

class ComponentInput(TypedDict):
    kind: BasePrizeKind
    name: str
    description: NotRequired[str]
    quantity: int
    amount: NotRequired[str | None]
    currency: NotRequired[str]

class InputOfComponentInput(TypedDict):
    kind: InputOfBasePrizeKind
    name: str
    description: NotRequired[str]
    quantity: int
    amount: NotRequired[str | None]
    currency: NotRequired[str]

class ComponentOutput(TypedDict):
    public_id: str
    kind: str
    name: str
    description: str
    quantity: int
    amount: str | None
    currency: str

class InputOfComponentOutput(TypedDict):
    public_id: str
    kind: str
    name: str
    description: str
    quantity: int
    amount: str | None
    currency: str

class ConfigHistoryEntrySchema(TypedDict):
    public_id: str
    actor: str | None
    action: str
    resource_type: str
    resource_id: str
    changes: Any
    created_at: str

class InputOfConfigHistoryEntrySchema(TypedDict):
    public_id: str
    actor: str | None
    action: str
    resource_type: str
    resource_id: str
    changes: Any
    created_at: str

class ConfigRestoreResultSchema(TypedDict):
    restored: bool
    resource_type: str
    resource_id: str
    changes: Any

class InputOfConfigRestoreResultSchema(TypedDict):
    restored: bool
    resource_type: str
    resource_id: str
    changes: Any

class ConflictOfInterest(TypedDict):
    public_id: str
    judge: str
    project: str
    reason: NotRequired[str]
    created_at: str

class InputOfConflictOfInterest(TypedDict):
    reason: NotRequired[str]

class ConformanceReportOutput(TypedDict):
    event: str
    generated_at: str
    conformance_claimed: bool
    standard: str
    theme: dict[str, Any]
    summary: dict[str, int]
    pages: list[dict[str, Any]]
    manual_review: list[dict[str, Any]]

class InputOfConformanceReportOutput(TypedDict):
    event: str
    generated_at: str
    conformance_claimed: bool
    standard: str
    theme: dict[str, Any]
    summary: dict[str, int]
    pages: list[dict[str, Any]]
    manual_review: list[dict[str, Any]]

class CreateTeamInput(TypedDict):
    name: str

class InputOfCreateTeamInput(TypedDict):
    name: str

class CreateTeamInviteInput(TypedDict):
    max_uses: NotRequired[int]

class InputOfCreateTeamInviteInput(TypedDict):
    max_uses: NotRequired[int]

class CredentialCreateSchema(TypedDict):
    name: str
    allowed_actions: list[str]
    event: NotRequired[str | None]
    expires_in_days: NotRequired[int]

class InputOfCredentialCreateSchema(TypedDict):
    name: str
    allowed_actions: list[str]
    event: NotRequired[str | None]
    expires_in_days: NotRequired[int]

class CredentialIssuedSchema(TypedDict):
    public_id: str
    name: str
    workspace: str
    event: str | None
    allowed_actions: list[str]
    created_at: str
    expires_at: str
    revoked_at: str | None
    token: str

class InputOfCredentialIssuedSchema(TypedDict):
    public_id: str
    name: str
    workspace: str
    event: str | None
    allowed_actions: list[str]
    created_at: str
    expires_at: str
    revoked_at: str | None
    token: str

class CredentialReadSchema(TypedDict):
    public_id: str
    name: str
    workspace: str
    event: str | None
    allowed_actions: list[str]
    created_at: str
    expires_at: str
    revoked_at: str | None

class InputOfCredentialReadSchema(TypedDict):
    public_id: str
    name: str
    workspace: str
    event: str | None
    allowed_actions: list[str]
    created_at: str
    expires_at: str
    revoked_at: str | None

class DecisionInput(TypedDict):
    decision: DecisionInputDecisionEnum
    note: NotRequired[str]

class InputOfDecisionInput(TypedDict):
    decision: InputOfDecisionInputDecisionEnum
    note: NotRequired[str]

DecisionInputDecisionEnum = Literal['pending', 'needs_remediation', 'cleared', 'ineligible']

InputOfDecisionInputDecisionEnum = Literal['pending', 'needs_remediation', 'cleared', 'ineligible']

class DeliveryInspection(TypedDict):
    public_id: str
    event_id: str
    event_type: str
    status: str
    attempts: int
    last_status_code: int | None
    last_error: str
    next_attempt_at: str | None
    created_at: str
    completed_at: str | None
    destination: str
    next_body: str
    body_sha256: str
    signature_scheme: str
    history: list[AttemptOutput]
    history_has_more: bool

class InputOfDeliveryInspection(TypedDict):
    public_id: str
    event_id: str
    event_type: str
    status: str
    attempts: int
    last_status_code: int | None
    last_error: str
    next_attempt_at: str | None
    created_at: str
    completed_at: str | None
    destination: str
    next_body: str
    body_sha256: str
    signature_scheme: str
    history: list[InputOfAttemptOutput]
    history_has_more: bool

class DeliveryOutput(TypedDict):
    public_id: str
    event_id: str
    event_type: str
    status: str
    attempts: int
    last_status_code: int | None
    last_error: str
    next_attempt_at: str | None
    created_at: str
    completed_at: str | None

class InputOfDeliveryOutput(TypedDict):
    public_id: str
    event_id: str
    event_type: str
    status: str
    attempts: int
    last_status_code: int | None
    last_error: str
    next_attempt_at: str | None
    created_at: str
    completed_at: str | None

DispositionEnum = Literal['dismiss', 'escalate', 'resolve', 'hide', 'acknowledge', 'approve', 'reject', 'waitlist']

InputOfDispositionEnum = Literal['dismiss', 'escalate', 'resolve', 'hide', 'acknowledge', 'approve', 'reject', 'waitlist']

class DropoutCoverageGapSchema(TypedDict):
    project: str
    missing: int

class InputOfDropoutCoverageGapSchema(TypedDict):
    project: str
    missing: int

class DropoutScenarioSchema(TypedDict):
    drop_judges: list[str]
    evidence: dict[str, Any]
    pending_removed: int
    assignments_added: int
    coverage_gaps: list[DropoutCoverageGapSchema]

class InputOfDropoutScenarioSchema(TypedDict):
    drop_judges: list[str]
    evidence: dict[str, Any]
    pending_removed: int
    assignments_added: int
    coverage_gaps: list[InputOfDropoutCoverageGapSchema]

class DropoutSimulationInputSchema(TypedDict):
    drop_scenarios: list[list[str]]

class InputOfDropoutSimulationInputSchema(TypedDict):
    drop_scenarios: list[list[str]]

class DropoutSimulationSchema(TypedDict):
    active_version: str
    baseline: dict[str, Any]
    scenarios: list[DropoutScenarioSchema]

class InputOfDropoutSimulationSchema(TypedDict):
    active_version: str
    baseline: dict[str, Any]
    scenarios: list[InputOfDropoutScenarioSchema]

class EmailTokenInputSchema(TypedDict):
    email: str

class InputOfEmailTokenInputSchema(TypedDict):
    email: str

class EmailTokenReceiptSchema(TypedDict):
    token: str
    expires_at: str

class InputOfEmailTokenReceiptSchema(TypedDict):
    token: str
    expires_at: str

class ErrorSchema(TypedDict):
    detail: str

class InputOfErrorSchema(TypedDict):
    detail: str

class EvaluationPlan(TypedDict):
    public_id: str
    name: str
    candidate_type: NotRequired[CandidateTypeEnum]
    pool_strategy: NotRequired[PoolStrategyEnum]
    mode: NotRequired[EvaluationPlanModeEnum]
    results_visible_to_participants: NotRequired[bool]
    feedback_visible_to_participants: NotRequired[bool]
    feedback_anonymous: NotRequired[bool]
    draft_criteria: NotRequired[Any]
    pool: NotRequired[str | None]
    hybrid_source: NotRequired[str | None]
    current_rubric_version: int | None
    active_assignment_version: int | None
    published_normalization_run: int | None
    published_pairwise_run: int | None
    calibration_projects: list[str]
    calibration_required: NotRequired[bool]
    blind_judging: NotRequired[bool]
    prize_judging: NotRequired[bool]
    created_at: str
    updated_at: str

class InputOfEvaluationPlan(TypedDict):
    name: str
    candidate_type: NotRequired[InputOfCandidateTypeEnum]
    pool_strategy: NotRequired[InputOfPoolStrategyEnum]
    mode: NotRequired[InputOfEvaluationPlanModeEnum]
    results_visible_to_participants: NotRequired[bool]
    feedback_visible_to_participants: NotRequired[bool]
    feedback_anonymous: NotRequired[bool]
    draft_criteria: NotRequired[Any]
    pool: NotRequired[str | None]
    hybrid_source: NotRequired[str | None]
    calibration_required: NotRequired[bool]
    blind_judging: NotRequired[bool]
    prize_judging: NotRequired[bool]

EvaluationPlanModeEnum = Literal['rubric', 'pairwise']

InputOfEvaluationPlanModeEnum = Literal['rubric', 'pairwise']

class EvaluationPool(TypedDict):
    public_id: str
    name: str
    created_at: str

class InputOfEvaluationPool(TypedDict):
    name: str

class EvaluationProgressSchema(TypedDict):
    candidate_count: int
    pool_judge_count: int
    conflict_count: int
    expected_ballots: int | None
    submitted_ballots: int
    completion_ratio: float | None
    rubric_published: bool
    assignment_active: bool
    latest_normalization_run: NormalizationProgressSchema | None
    results_published: bool
    calibration: CalibrationOverviewSchema | None

class InputOfEvaluationProgressSchema(TypedDict):
    candidate_count: int
    pool_judge_count: int
    conflict_count: int
    expected_ballots: int | None
    submitted_ballots: int
    completion_ratio: float | None
    rubric_published: bool
    assignment_active: bool
    latest_normalization_run: InputOfNormalizationProgressSchema | None
    results_published: bool
    calibration: InputOfCalibrationOverviewSchema | None

class Event(TypedDict):
    public_id: str
    name: str
    slug: str
    description: NotRequired[str]
    timezone: NotRequired[str]
    starts_at: NotRequired[str | None]
    ends_at: NotRequired[str | None]
    status: EventStatus
    is_public: NotRequired[bool]
    created_at: str
    updated_at: str

class InputOfEvent(TypedDict):
    name: str
    slug: str
    description: NotRequired[str]
    timezone: NotRequired[str]
    starts_at: NotRequired[str | None]
    ends_at: NotRequired[str | None]
    is_public: NotRequired[bool]

class EventAnalyticsResponse(TypedDict):
    event: str
    generated_at: str
    registration: Any
    teams: Any
    submissions: Any
    judging: Any
    voting: Any

class InputOfEventAnalyticsResponse(TypedDict):
    event: str
    generated_at: str
    registration: Any
    teams: Any
    submissions: Any
    judging: Any
    voting: Any

class EventApplication(TypedDict):
    public_id: str
    user: str
    username: str
    status: EventApplicationStatusEnum
    note: str
    waitlist_position: int | None
    decided_by: str | None
    decided_at: str | None
    created_at: str

class InputOfEventApplication(TypedDict):
    pass

EventApplicationStatusEnum = Literal['pending', 'approved', 'waitlisted', 'rejected']

InputOfEventApplicationStatusEnum = Literal['pending', 'approved', 'waitlisted', 'rejected']

class EventDashboardSchema(TypedDict):
    event: Event
    track_count: int
    base_prize_count: int
    configuration_checks: list[str]

class InputOfEventDashboardSchema(TypedDict):
    event: InputOfEvent
    track_count: int
    base_prize_count: int
    configuration_checks: list[str]

EventQuestionStatus = Literal['pending', 'published', 'hidden']

InputOfEventQuestionStatus = Literal['pending', 'published', 'hidden']

EventStatus = Literal['draft', 'open', 'closed', 'archived']

InputOfEventStatus = Literal['draft', 'open', 'closed', 'archived']

class EventStatusInput(TypedDict):
    status: EventStatus

class InputOfEventStatusInput(TypedDict):
    status: InputOfEventStatus

class EventTemplateCreateInput(TypedDict):
    event: str
    name: str
    sections: NotRequired[list[str]]

class InputOfEventTemplateCreateInput(TypedDict):
    event: str
    name: str
    sections: NotRequired[list[str]]

class EventTemplateOutput(TypedDict):
    public_id: str
    name: str
    source_event_name: str
    sections: list[str]
    created_at: str

class InputOfEventTemplateOutput(TypedDict):
    public_id: str
    name: str
    source_event_name: str
    sections: list[str]
    created_at: str

class ExceptionGrant(TypedDict):
    public_id: str
    action: ActionEnum
    subject_type: str
    subject_id: str
    scope: NotRequired[str]
    reason: NotRequired[str]
    granted_at: str
    expires_at: NotRequired[str | None]

class InputOfExceptionGrant(TypedDict):
    action: InputOfActionEnum
    subject_type: str
    subject_id: str
    scope: NotRequired[str]
    reason: NotRequired[str]
    expires_at: NotRequired[str | None]

class ExpertiseInputSchema(TypedDict):
    tags: list[str]

class InputOfExpertiseInputSchema(TypedDict):
    tags: list[str]

class ExpertiseOutputSchema(TypedDict):
    judge: str
    tags: list[str]
    updated_at: str | None

class InputOfExpertiseOutputSchema(TypedDict):
    judge: str
    tags: list[str]
    updated_at: str | None

class ExternalArtifactInputSchema(TypedDict):
    kind: str
    visibility: str
    title: NotRequired[str]
    external_url: str

class InputOfExternalArtifactInputSchema(TypedDict):
    kind: str
    visibility: str
    title: NotRequired[str]
    external_url: str

class FeedbackEntrySchema(TypedDict):
    judge: str | None
    comment: str
    submitted_at: str

class InputOfFeedbackEntrySchema(TypedDict):
    judge: str | None
    comment: str
    submitted_at: str

class FinalizeInput(TypedDict):
    winners: list[str]
    override_reason: NotRequired[str]

class InputOfFinalizeInput(TypedDict):
    winners: list[str]
    override_reason: NotRequired[str]

class FindingInput(TypedDict):
    message: str
    severity: NotRequired[SeverityEnum]

class InputOfFindingInput(TypedDict):
    message: str
    severity: NotRequired[InputOfSeverityEnum]

class FindingOutput(TypedDict):
    public_id: str
    code: str
    automated: bool
    severity: str
    message: str
    state: str
    participant_response: str
    resolution_note: str
    opened_at: str
    addressed_at: str | None
    closed_at: str | None

class InputOfFindingOutput(TypedDict):
    public_id: str
    code: str
    automated: bool
    severity: str
    message: str
    state: str
    participant_response: str
    resolution_note: str
    opened_at: str
    addressed_at: str | None
    closed_at: str | None

class FormAnswersInputSchema(TypedDict):
    answers: Any

class InputOfFormAnswersInputSchema(TypedDict):
    answers: Any

class FormDraftInputSchema(TypedDict):
    schema: Any

class InputOfFormDraftInputSchema(TypedDict):
    schema: Any

class FormNameInputSchema(TypedDict):
    name: str

class InputOfFormNameInputSchema(TypedDict):
    name: str

class FormPayloadSchema(TypedDict):
    public_id: str
    name: str
    stage: str | None
    draft_schema: Any

class InputOfFormPayloadSchema(TypedDict):
    public_id: str
    name: str
    stage: str | None
    draft_schema: Any

class FormResponseSchema(TypedDict):
    version: str
    answers: Any

class InputOfFormResponseSchema(TypedDict):
    version: str
    answers: Any

class FormVersionSchema(TypedDict):
    public_id: str
    number: int
    schema: Any
    published_at: str

class InputOfFormVersionSchema(TypedDict):
    public_id: str
    number: int
    schema: Any
    published_at: str

FulfillmentInputStateEnum = Literal['pending', 'contacted', 'verified', 'sent', 'claimed', 'failed']

InputOfFulfillmentInputStateEnum = Literal['pending', 'contacted', 'verified', 'sent', 'claimed', 'failed']

class FulfillmentOutput(TypedDict):
    public_id: str
    component: str
    component_name: str
    state: str
    note: str
    updated_at: str

class InputOfFulfillmentOutput(TypedDict):
    public_id: str
    component: str
    component_name: str
    state: str
    note: str
    updated_at: str

class GalleryItemOutput(TypedDict):
    public_id: str
    name: str
    description: str
    track: str | None
    team: str | None
    url: str

class InputOfGalleryItemOutput(TypedDict):
    public_id: str
    name: str
    description: str
    track: str | None
    team: str | None
    url: str

class GalleryProjectSchema(TypedDict):
    id: str
    title: str
    summary: str
    team: str
    track: str
    repo_url: str

class InputOfGalleryProjectSchema(TypedDict):
    id: str
    title: str
    summary: str
    team: str
    track: str
    repo_url: str

class GraphValidationSchema(TypedDict):
    valid: bool
    order: NotRequired[list[str]]
    errors: NotRequired[list[str]]

class InputOfGraphValidationSchema(TypedDict):
    valid: bool
    order: NotRequired[list[str]]
    errors: NotRequired[list[str]]

class HealthResponse(TypedDict):
    status: str

class InputOfHealthResponse(TypedDict):
    status: str

IdentityModeEnum = Literal['authenticated', 'email_link', 'token']

InputOfIdentityModeEnum = Literal['authenticated', 'email_link', 'token']

class ImportedEventOutput(TypedDict):
    public_id: str
    name: str
    slug: str

class InputOfImportedEventOutput(TypedDict):
    public_id: str
    name: str
    slug: str

class InboxMessageSchema(TypedDict):
    public_id: str
    subject: str
    body: str
    event: str
    event_name: str
    created_at: str
    read_at: str | None

class InputOfInboxMessageSchema(TypedDict):
    public_id: str
    subject: str
    body: str
    event: str
    event_name: str
    created_at: str
    read_at: str | None

class InstantiateInput(TypedDict):
    name: str
    slug: str

class InputOfInstantiateInput(TypedDict):
    name: str
    slug: str

class JudgeCOIRelationship(TypedDict):
    public_id: str
    judge: str
    kind: COIRelationshipKind
    team: str | None
    value: NotRequired[str]
    declared_by: str
    created_at: str

class InputOfJudgeCOIRelationship(TypedDict):
    kind: InputOfCOIRelationshipKind
    value: NotRequired[str]

class JudgeCOIRelationshipInputSchema(TypedDict):
    judge: NotRequired[str]
    kind: COIRelationshipKind
    team: NotRequired[str]
    value: NotRequired[str]

class InputOfJudgeCOIRelationshipInputSchema(TypedDict):
    judge: NotRequired[str]
    kind: InputOfCOIRelationshipKind
    team: NotRequired[str]
    value: NotRequired[str]

class JudgeCalendarSchema(TypedDict):
    windows: list[CalendarWindowSchema]
    assignments: list[CalendarAssignmentSchema]

class InputOfJudgeCalendarSchema(TypedDict):
    windows: list[InputOfCalendarWindowSchema]
    assignments: list[InputOfCalendarAssignmentSchema]

class JudgeDirectorySchema(TypedDict):
    judge: str
    username: str

class InputOfJudgeDirectorySchema(TypedDict):
    judge: str
    username: str

class JudgeEventSummary(TypedDict):
    public_id: str
    name: str

class InputOfJudgeEventSummary(TypedDict):
    public_id: str
    name: str

class JudgeInvitationDecisionSchema(TypedDict):
    decision: JudgeInvitationDecisionSchemaDecisionEnum

class InputOfJudgeInvitationDecisionSchema(TypedDict):
    decision: InputOfJudgeInvitationDecisionSchemaDecisionEnum

JudgeInvitationDecisionSchemaDecisionEnum = Literal['accept', 'decline']

InputOfJudgeInvitationDecisionSchemaDecisionEnum = Literal['accept', 'decline']

class JudgeInvitationInputSchema(TypedDict):
    pool: str
    judge: str

class InputOfJudgeInvitationInputSchema(TypedDict):
    pool: str
    judge: str

class JudgeInvitationSchema(TypedDict):
    public_id: str
    event: str
    event_name: str
    pool: str
    pool_name: str
    judge: str
    judge_username: str
    status: JudgeInvitationSchemaStatusEnum
    created_at: str
    responded_at: str | None

class InputOfJudgeInvitationSchema(TypedDict):
    public_id: str
    event: str
    event_name: str
    pool: str
    pool_name: str
    judge: str
    judge_username: str
    status: InputOfJudgeInvitationSchemaStatusEnum
    created_at: str
    responded_at: str | None

JudgeInvitationSchemaStatusEnum = Literal['pending', 'accepted', 'declined', 'revoked']

InputOfJudgeInvitationSchemaStatusEnum = Literal['pending', 'accepted', 'declined', 'revoked']

class JudgeRecordInput(TypedDict):
    user: str

class InputOfJudgeRecordInput(TypedDict):
    user: str

class JudgeScoreSchema(TypedDict):
    project: str
    comment: str
    criteria: dict[str, int]

class InputOfJudgeScoreSchema(TypedDict):
    project: str
    comment: str
    criteria: dict[str, int]

class JudgeSuggestionSchema(TypedDict):
    rank: int
    judge: str
    username: str
    expertise_tags: list[str]
    matched_tags: list[str]
    events_judged: int
    ballots_completed: int
    assignments_received: int
    completion_rate: float | None

class InputOfJudgeSuggestionSchema(TypedDict):
    rank: int
    judge: str
    username: str
    expertise_tags: list[str]
    matched_tags: list[str]
    events_judged: int
    ballots_completed: int
    assignments_received: int
    completion_rate: float | None

class JudgeWorkloadRowSchema(TypedDict):
    judge: str
    assigned_count: int
    submitted_count: int
    completion_ratio: float

class InputOfJudgeWorkloadRowSchema(TypedDict):
    judge: str
    assigned_count: int
    submitted_count: int
    completion_ratio: float

class LaunchChecklistSchema(TypedDict):
    status: str
    items: list[ChecklistItemSchema]

class InputOfLaunchChecklistSchema(TypedDict):
    status: str
    items: list[InputOfChecklistItemSchema]

class LibraryTemplateOutput(TypedDict):
    slug: str
    label: str
    description: str
    tracks: list[str]
    stages: list[str]

class InputOfLibraryTemplateOutput(TypedDict):
    slug: str
    label: str
    description: str
    tracks: list[str]
    stages: list[str]

class LocationInput(TypedDict):
    kind: LocationKind
    name: str
    parent: NotRequired[str | None]
    capacity: NotRequired[int | None]
    x: NotRequired[float | None]
    y: NotRequired[float | None]
    notes: NotRequired[str]
    position: NotRequired[int]

class InputOfLocationInput(TypedDict):
    kind: InputOfLocationKind
    name: str
    parent: NotRequired[str | None]
    capacity: NotRequired[int | None]
    x: NotRequired[float | None]
    y: NotRequired[float | None]
    notes: NotRequired[str]
    position: NotRequired[int]

LocationKind = Literal['room', 'table', 'booth']

InputOfLocationKind = Literal['room', 'table', 'booth']

class LocationOutput(TypedDict):
    public_id: str
    kind: str
    name: str
    parent: str | None
    capacity: int | None
    x: float | None
    y: float | None
    notes: str
    position: int
    assigned: int

class InputOfLocationOutput(TypedDict):
    public_id: str
    kind: str
    name: str
    parent: str | None
    capacity: int | None
    x: float | None
    y: float | None
    notes: str
    position: int
    assigned: int

class LoginInputSchema(TypedDict):
    username: str
    password: str

class InputOfLoginInputSchema(TypedDict):
    username: str
    password: str

class LoginResponseSchema(TypedDict):
    user: UserSummarySchema

class InputOfLoginResponseSchema(TypedDict):
    user: InputOfUserSummarySchema

class MarketplaceProfileInput(TypedDict):
    skills: list[str]
    roles: NotRequired[list[str]]
    interests: NotRequired[list[str]]
    availability_hours_per_week: NotRequired[int | None]
    bio: NotRequired[str]
    visible: bool

class InputOfMarketplaceProfileInput(TypedDict):
    skills: list[str]
    roles: NotRequired[list[str]]
    interests: NotRequired[list[str]]
    availability_hours_per_week: NotRequired[int | None]
    bio: NotRequired[str]
    visible: bool

class MarketplaceProfileSchema(TypedDict):
    public_id: str
    user: str
    username: str
    skills: list[str]
    roles: list[str]
    interests: list[str]
    availability_hours_per_week: int | None
    bio: str
    visible: bool
    matched_skills: NotRequired[list[str]]
    matched_roles: NotRequired[list[str]]
    matched_interests: NotRequired[list[str]]
    availability_compatible: NotRequired[bool | None]

class InputOfMarketplaceProfileSchema(TypedDict):
    public_id: str
    user: str
    username: str
    skills: list[str]
    roles: list[str]
    interests: list[str]
    availability_hours_per_week: int | None
    bio: str
    visible: bool
    matched_skills: NotRequired[list[str]]
    matched_roles: NotRequired[list[str]]
    matched_interests: NotRequired[list[str]]
    availability_compatible: NotRequired[bool | None]

class MembershipInputSchema(TypedDict):
    username: str
    role: str

class InputOfMembershipInputSchema(TypedDict):
    username: str
    role: str

class MembershipSchema(TypedDict):
    public_id: str
    user: str
    role: str

class InputOfMembershipSchema(TypedDict):
    public_id: str
    user: str
    role: str

class MembershipSummarySchema(TypedDict):
    workspace: str
    workspace_name: str
    workspace_slug: str
    role: str

class InputOfMembershipSummarySchema(TypedDict):
    workspace: str
    workspace_name: str
    workspace_slug: str
    role: str

class MentorNote(TypedDict):
    public_id: str
    mentor: str
    mentor_username: str
    body: str
    created_at: str

class InputOfMentorNote(TypedDict):
    body: str

class MentorNoteInputSchema(TypedDict):
    body: str

class InputOfMentorNoteInputSchema(TypedDict):
    body: str

class MessageInputSchema(TypedDict):
    subject: str
    body: str
    audience_kind: str
    audience_params: NotRequired[Any]

class InputOfMessageInputSchema(TypedDict):
    subject: str
    body: str
    audience_kind: str
    audience_params: NotRequired[Any]

class MessageSchema(TypedDict):
    public_id: str
    subject: str
    body: str
    audience_kind: str
    audience_params: Any
    recipient_count: int
    email_failure_count: int
    created_at: str

class InputOfMessageSchema(TypedDict):
    public_id: str
    subject: str
    body: str
    audience_kind: str
    audience_params: Any
    recipient_count: int
    email_failure_count: int
    created_at: str

MethodEnum = Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

InputOfMethodEnum = Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

class ModerationQueueResponse(TypedDict):
    sections: list[Any]

class InputOfModerationQueueResponse(TypedDict):
    sections: list[Any]

class ModerationReviewInput(TypedDict):
    kind: ModerationReviewInputKindEnum
    source_key: str
    evidence_digest: str
    disposition: DispositionEnum
    note: str

class InputOfModerationReviewInput(TypedDict):
    kind: InputOfModerationReviewInputKindEnum
    source_key: str
    evidence_digest: str
    disposition: InputOfDispositionEnum
    note: str

ModerationReviewInputKindEnum = Literal['duplicate', 'voting', 'content', 'artifact', 'eligibility']

InputOfModerationReviewInputKindEnum = Literal['duplicate', 'voting', 'content', 'artifact', 'eligibility']

class ModerationReviewResponse(TypedDict):
    public_id: str
    kind: str
    source_key: str
    evidence_digest: str
    evidence: Any
    disposition: str
    note: str
    actor: str
    created_at: str

class InputOfModerationReviewResponse(TypedDict):
    public_id: str
    kind: str
    source_key: str
    evidence_digest: str
    evidence: Any
    disposition: str
    note: str
    actor: str
    created_at: str

class MyEventApplicationResponse(TypedDict):
    application: EventApplication | None

class InputOfMyEventApplicationResponse(TypedDict):
    application: InputOfEventApplication | None

class MyMarketplaceProfileResponse(TypedDict):
    profile: MarketplaceProfileSchema | None

class InputOfMyMarketplaceProfileResponse(TypedDict):
    profile: InputOfMarketplaceProfileSchema | None

class MyTeamResponse(TypedDict):
    team: Team | None
    my_role: str | None

class InputOfMyTeamResponse(TypedDict):
    team: InputOfTeam | None
    my_role: str | None

class NormalizationInputSchema(TypedDict):
    ridge_lambda: NotRequired[float]

class InputOfNormalizationInputSchema(TypedDict):
    ridge_lambda: NotRequired[float]

class NormalizationProgressSchema(TypedDict):
    number: int
    converged: bool
    low_information_judges: int

class InputOfNormalizationProgressSchema(TypedDict):
    number: int
    converged: bool
    low_information_judges: int

class NormalizationRun(TypedDict):
    public_id: str
    number: int
    ridge_lambda: float
    iterations: int
    converged: bool
    grand_mean: float
    evidence: Any
    created_at: str

class InputOfNormalizationRun(TypedDict):
    number: int
    ridge_lambda: float
    iterations: int
    converged: bool
    grand_mean: float
    evidence: Any

class NoteInput(TypedDict):
    body: str
    project: NotRequired[str]

class InputOfNoteInput(TypedDict):
    body: str
    project: NotRequired[str]

class OpenInput(TypedDict):
    quorum: NotRequired[int]

class InputOfOpenInput(TypedDict):
    quorum: NotRequired[int]

class OperationsSummarySchema(TypedDict):
    participants: Any
    submissions: Any
    judging: Any
    stages: Any
    publication: Any
    moderation: Any

class InputOfOperationsSummarySchema(TypedDict):
    participants: Any
    submissions: Any
    judging: Any
    stages: Any
    publication: Any
    moderation: Any

class OperatorActivitySchema(TypedDict):
    action: str
    actor: str | None
    target_type: str
    target_id: str
    created_at: str

class InputOfOperatorActivitySchema(TypedDict):
    action: str
    actor: str | None
    target_type: str
    target_id: str
    created_at: str

class OperatorConsoleSchema(TypedDict):
    event_total: int
    events: list[OperatorEventSchema]
    template_total: int
    templates: list[OperatorTemplateSchema]
    activity: list[OperatorActivitySchema]

class InputOfOperatorConsoleSchema(TypedDict):
    event_total: int
    events: list[InputOfOperatorEventSchema]
    template_total: int
    templates: list[InputOfOperatorTemplateSchema]
    activity: list[InputOfOperatorActivitySchema]

class OperatorEventSchema(TypedDict):
    public_id: str
    name: str
    status: str
    is_public: bool
    updated_at: str
    health: str
    blocker_count: int
    warning_count: int

class InputOfOperatorEventSchema(TypedDict):
    public_id: str
    name: str
    status: str
    is_public: bool
    updated_at: str
    health: str
    blocker_count: int
    warning_count: int

class OperatorTemplateSchema(TypedDict):
    public_id: str
    name: str
    source_event_name: str

class InputOfOperatorTemplateSchema(TypedDict):
    public_id: str
    name: str
    source_event_name: str

class Page(TypedDict):
    public_id: str
    theme: NotRequired[ThemeEnum]
    created_at: str
    updated_at: str

class InputOfPage(TypedDict):
    theme: NotRequired[InputOfThemeEnum]

class PageBlock(TypedDict):
    public_id: str
    kind: PageBlockKindEnum
    position: NotRequired[int]
    config: NotRequired[Any]
    created_at: str
    updated_at: str

class InputOfPageBlock(TypedDict):
    kind: InputOfPageBlockKindEnum
    position: NotRequired[int]
    config: NotRequired[Any]

PageBlockKindEnum = Literal['hero', 'tracks', 'prizes', 'schedule', 'sponsors', 'faq', 'resources', 'gallery', 'results', 'announcements', 'rich_text', 'cta']

InputOfPageBlockKindEnum = Literal['hero', 'tracks', 'prizes', 'schedule', 'sponsors', 'faq', 'resources', 'gallery', 'results', 'announcements', 'rich_text', 'cta']

class PageBlockOrderInput(TypedDict):
    block_ids: list[str]

class InputOfPageBlockOrderInput(TypedDict):
    block_ids: list[str]

class PairwiseComparison(TypedDict):
    public_id: str
    judge: str
    project_a: str
    project_b: str
    winner: str | None
    submitted_at: str

class InputOfPairwiseComparison(TypedDict):
    pass

class PairwiseComparisonInputSchema(TypedDict):
    project_a: str
    project_b: str
    winner: NotRequired[str | None]

class InputOfPairwiseComparisonInputSchema(TypedDict):
    project_a: str
    project_b: str
    winner: NotRequired[str | None]

class PairwiseNextPairSchema(TypedDict):
    project_a: str
    project_b: str

class InputOfPairwiseNextPairSchema(TypedDict):
    project_a: str
    project_b: str

class PairwiseRankedResultSchema(TypedDict):
    rank: int
    project: str | None
    project_name: str | None
    strength: float
    win_count: float
    comparison_count: float
    tie_break: int | None

class InputOfPairwiseRankedResultSchema(TypedDict):
    rank: int
    project: str | None
    project_name: str | None
    strength: float
    win_count: float
    comparison_count: float
    tie_break: int | None

class PairwiseResultsPublishInputSchema(TypedDict):
    pairwise_run: str
    tie_breaks: NotRequired[dict[str, int]]

class InputOfPairwiseResultsPublishInputSchema(TypedDict):
    pairwise_run: str
    tie_breaks: NotRequired[dict[str, int]]

class PairwiseRun(TypedDict):
    public_id: str
    number: int
    prior_games: float
    iterations: int
    converged: bool
    evidence: Any
    created_at: str

class InputOfPairwiseRun(TypedDict):
    number: int
    prior_games: float
    iterations: int
    converged: bool
    evidence: Any

class PairwiseRunInputSchema(TypedDict):
    prior_games: NotRequired[float]

class InputOfPairwiseRunInputSchema(TypedDict):
    prior_games: NotRequired[float]

class ParticipantEventSummary(TypedDict):
    public_id: str
    name: str

class InputOfParticipantEventSummary(TypedDict):
    public_id: str
    name: str

class ParticipantFormSchema(TypedDict):
    public_id: str
    name: str
    stage: str | None
    number: int
    schema: Any

class InputOfParticipantFormSchema(TypedDict):
    public_id: str
    name: str
    stage: str | None
    number: int
    schema: Any

ParticipationModeEnum = Literal['individual', 'team_formation', 'team_locked']

InputOfParticipationModeEnum = Literal['individual', 'team_formation', 'team_locked']

class PatchedBasePrize(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    description: NotRequired[str]
    kind: NotRequired[BasePrizeKind]
    amount: NotRequired[str | None]
    currency: NotRequired[str]
    track: NotRequired[str | None]
    position: NotRequired[int]

class InputOfPatchedBasePrize(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str]
    kind: NotRequired[InputOfBasePrizeKind]
    amount: NotRequired[str | None]
    currency: NotRequired[str]
    track: NotRequired[str | None]
    position: NotRequired[int]

class PatchedEvaluationPlan(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    candidate_type: NotRequired[CandidateTypeEnum]
    pool_strategy: NotRequired[PoolStrategyEnum]
    mode: NotRequired[EvaluationPlanModeEnum]
    results_visible_to_participants: NotRequired[bool]
    feedback_visible_to_participants: NotRequired[bool]
    feedback_anonymous: NotRequired[bool]
    draft_criteria: NotRequired[Any]
    pool: NotRequired[str | None]
    hybrid_source: NotRequired[str | None]
    current_rubric_version: NotRequired[int | None]
    active_assignment_version: NotRequired[int | None]
    published_normalization_run: NotRequired[int | None]
    published_pairwise_run: NotRequired[int | None]
    calibration_projects: NotRequired[list[str]]
    calibration_required: NotRequired[bool]
    blind_judging: NotRequired[bool]
    prize_judging: NotRequired[bool]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]

class InputOfPatchedEvaluationPlan(TypedDict):
    name: NotRequired[str]
    candidate_type: NotRequired[InputOfCandidateTypeEnum]
    pool_strategy: NotRequired[InputOfPoolStrategyEnum]
    mode: NotRequired[InputOfEvaluationPlanModeEnum]
    results_visible_to_participants: NotRequired[bool]
    feedback_visible_to_participants: NotRequired[bool]
    feedback_anonymous: NotRequired[bool]
    draft_criteria: NotRequired[Any]
    pool: NotRequired[str | None]
    hybrid_source: NotRequired[str | None]
    calibration_required: NotRequired[bool]
    blind_judging: NotRequired[bool]
    prize_judging: NotRequired[bool]

class PatchedEvent(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    slug: NotRequired[str]
    description: NotRequired[str]
    timezone: NotRequired[str]
    starts_at: NotRequired[str | None]
    ends_at: NotRequired[str | None]
    status: NotRequired[EventStatus]
    is_public: NotRequired[bool]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]

class InputOfPatchedEvent(TypedDict):
    name: NotRequired[str]
    slug: NotRequired[str]
    description: NotRequired[str]
    timezone: NotRequired[str]
    starts_at: NotRequired[str | None]
    ends_at: NotRequired[str | None]
    is_public: NotRequired[bool]

class PatchedFulfillmentInput(TypedDict):
    state: NotRequired[FulfillmentInputStateEnum]
    note: NotRequired[str]

class InputOfPatchedFulfillmentInput(TypedDict):
    state: NotRequired[InputOfFulfillmentInputStateEnum]
    note: NotRequired[str]

class PatchedLocationPatchInput(TypedDict):
    kind: NotRequired[LocationKind]
    name: NotRequired[str]
    parent: NotRequired[str | None]
    capacity: NotRequired[int | None]
    x: NotRequired[float | None]
    y: NotRequired[float | None]
    notes: NotRequired[str]
    position: NotRequired[int]

class InputOfPatchedLocationPatchInput(TypedDict):
    kind: NotRequired[InputOfLocationKind]
    name: NotRequired[str]
    parent: NotRequired[str | None]
    capacity: NotRequired[int | None]
    x: NotRequired[float | None]
    y: NotRequired[float | None]
    notes: NotRequired[str]
    position: NotRequired[int]

class PatchedPage(TypedDict):
    public_id: NotRequired[str]
    theme: NotRequired[ThemeEnum]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]

class InputOfPatchedPage(TypedDict):
    theme: NotRequired[InputOfThemeEnum]

class PatchedPageBlock(TypedDict):
    public_id: NotRequired[str]
    kind: NotRequired[PageBlockKindEnum]
    position: NotRequired[int]
    config: NotRequired[Any]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]

class InputOfPatchedPageBlock(TypedDict):
    kind: NotRequired[InputOfPageBlockKindEnum]
    position: NotRequired[int]
    config: NotRequired[Any]

class PatchedPolicy(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    ast: NotRequired[Any]
    preset: NotRequired[str]
    preset_params: NotRequired[dict[str, Any]]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]

class InputOfPatchedPolicy(TypedDict):
    name: NotRequired[str]
    ast: NotRequired[Any]
    preset: NotRequired[str]
    preset_params: NotRequired[dict[str, Any]]

class PatchedProjectPatchInputSchema(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str]
    track: NotRequired[str | None]

class InputOfPatchedProjectPatchInputSchema(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str]
    track: NotRequired[str | None]

class PatchedStage(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    position: NotRequired[int]
    is_initial: NotRequired[bool]
    participation_mode: NotRequired[ParticipationModeEnum]
    created_at: NotRequired[str]

class InputOfPatchedStage(TypedDict):
    name: NotRequired[str]
    position: NotRequired[int]
    is_initial: NotRequired[bool]
    participation_mode: NotRequired[InputOfParticipationModeEnum]

class PatchedSubscriptionUpdate(TypedDict):
    enabled: NotRequired[bool]
    url: NotRequired[str]

class InputOfPatchedSubscriptionUpdate(TypedDict):
    enabled: NotRequired[bool]
    url: NotRequired[str]

class PatchedTaxonomyPatchInput(TypedDict):
    name: NotRequired[str]
    allows_multiple: NotRequired[bool]
    terms: NotRequired[list[TermInput]]

class InputOfPatchedTaxonomyPatchInput(TypedDict):
    name: NotRequired[str]
    allows_multiple: NotRequired[bool]
    terms: NotRequired[list[InputOfTermInput]]

class PatchedTeamOpeningInput(TypedDict):
    title: NotRequired[str]
    description: NotRequired[str]
    desired_skills: NotRequired[list[str]]
    desired_roles: NotRequired[list[str]]
    interests: NotRequired[list[str]]
    min_availability_hours_per_week: NotRequired[int | None]
    project: NotRequired[str | None]
    is_open: NotRequired[bool]

class InputOfPatchedTeamOpeningInput(TypedDict):
    title: NotRequired[str]
    description: NotRequired[str]
    desired_skills: NotRequired[list[str]]
    desired_roles: NotRequired[list[str]]
    interests: NotRequired[list[str]]
    min_availability_hours_per_week: NotRequired[int | None]
    project: NotRequired[str | None]
    is_open: NotRequired[bool]

class PatchedTemporalGate(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    opens_at: NotRequired[str | None]
    closes_at: NotRequired[str | None]
    event_local_opens_at: NotRequired[str | None]
    event_local_closes_at: NotRequired[str | None]
    dst_warning: NotRequired[str | None]
    created_at: NotRequired[str]

class InputOfPatchedTemporalGate(TypedDict):
    name: NotRequired[str]
    opens_at: NotRequired[str | None]
    closes_at: NotRequired[str | None]

class PatchedTrack(TypedDict):
    public_id: NotRequired[str]
    name: NotRequired[str]
    description: NotRequired[str]
    position: NotRequired[int]

class InputOfPatchedTrack(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str]
    position: NotRequired[int]

class PatchedVotingPlan(TypedDict):
    public_id: NotRequired[str]
    identity_mode: NotRequired[IdentityModeEnum]
    opens_at: NotRequired[str]
    closes_at: NotRequired[str]
    allow_comments: NotRequired[bool]
    comment_visibility: NotRequired[CommentVisibilityEnum]
    results_published_at: NotRequired[str | None]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]

class InputOfPatchedVotingPlan(TypedDict):
    identity_mode: NotRequired[InputOfIdentityModeEnum]
    opens_at: NotRequired[str]
    closes_at: NotRequired[str]
    allow_comments: NotRequired[bool]
    comment_visibility: NotRequired[InputOfCommentVisibilityEnum]

class PermissionMatrixEntrySchema(TypedDict):
    resource: str
    view: str
    path: str
    method: str
    access: AccessEnum
    roles: list[str]
    unrecognized: bool

class InputOfPermissionMatrixEntrySchema(TypedDict):
    resource: str
    view: str
    path: str
    method: str
    access: InputOfAccessEnum
    roles: list[str]
    unrecognized: bool

class PlacementInput(TypedDict):
    location: str | None

class InputOfPlacementInput(TypedDict):
    location: str | None

PlatformEnum = Literal['generic', 'discord', 'slack']

InputOfPlatformEnum = Literal['generic', 'discord', 'slack']

class Policy(TypedDict):
    public_id: str
    name: str
    ast: NotRequired[Any]
    preset: NotRequired[str]
    preset_params: NotRequired[dict[str, Any]]
    created_at: str
    updated_at: str

class InputOfPolicy(TypedDict):
    name: str
    ast: NotRequired[Any]
    preset: NotRequired[str]
    preset_params: NotRequired[dict[str, Any]]

class PolicyBinding(TypedDict):
    public_id: str
    action: ActionEnum
    policy: str
    created_at: str

class InputOfPolicyBinding(TypedDict):
    action: InputOfActionEnum
    policy: str

class PolicyDebugInput(TypedDict):
    action: ActionEnum
    subject_type: NotRequired[SubjectTypeEnum]
    subject_id: NotRequired[str]

class InputOfPolicyDebugInput(TypedDict):
    action: InputOfActionEnum
    subject_type: NotRequired[InputOfSubjectTypeEnum]
    subject_id: NotRequired[str]

class PolicyDebugResponse(TypedDict):
    action: ActionEnum
    subject_type: str | None
    subject_id: str | None
    checked_at: str
    facts: Any
    policy: Any
    policy_allowed: bool | None
    allowed: bool
    reason: str
    exception_grant_reason: str | None
    error: str | None
    trace: Any

class InputOfPolicyDebugResponse(TypedDict):
    action: InputOfActionEnum
    subject_type: str | None
    subject_id: str | None
    checked_at: str
    facts: Any
    policy: Any
    policy_allowed: bool | None
    allowed: bool
    reason: str
    exception_grant_reason: str | None
    error: str | None
    trace: Any

class PoolMembership(TypedDict):
    public_id: str
    judge: str
    track_expertise: list[str]
    created_at: str

class InputOfPoolMembership(TypedDict):
    pass

class PoolMembershipInputSchema(TypedDict):
    judge: str
    track_expertise: NotRequired[list[str]]

class InputOfPoolMembershipInputSchema(TypedDict):
    judge: str
    track_expertise: NotRequired[list[str]]

PoolStrategyEnum = Literal['all_judges', 'assigned_subset']

InputOfPoolStrategyEnum = Literal['all_judges', 'assigned_subset']

class PreflightCheckSchema(TypedDict):
    code: str
    severity: str
    detail: str

class InputOfPreflightCheckSchema(TypedDict):
    code: str
    severity: str
    detail: str

class PreflightSchema(TypedDict):
    status: str
    checks: list[PreflightCheckSchema]

class InputOfPreflightSchema(TypedDict):
    status: str
    checks: list[InputOfPreflightCheckSchema]

class PrivacyApplyInput(TypedDict):
    apply: NotRequired[bool]

class InputOfPrivacyApplyInput(TypedDict):
    apply: NotRequired[bool]

class PrivacyReportOutput(TypedDict):
    applied: bool
    erased: dict[str, Any]
    retained: NotRequired[dict[str, Any]]
    retained_reason: NotRequired[str]
    due: NotRequired[dict[str, Any]]

class InputOfPrivacyReportOutput(TypedDict):
    applied: bool
    erased: dict[str, Any]
    retained: NotRequired[dict[str, Any]]
    retained_reason: NotRequired[str]
    due: NotRequired[dict[str, Any]]

class Project(TypedDict):
    public_id: str
    name: str
    description: NotRequired[str]
    team: str | None
    track: str | None
    created_at: str
    updated_at: str
    members: list[ProjectMembership]

class InputOfProject(TypedDict):
    name: str
    description: NotRequired[str]

class ProjectCOIAttribute(TypedDict):
    public_id: str
    project: str
    kind: COIRelationshipKind
    value: str
    created_at: str

class InputOfProjectCOIAttribute(TypedDict):
    kind: InputOfCOIRelationshipKind
    value: str

class ProjectCOIAttributeInputSchema(TypedDict):
    project: str
    kind: ProjectCOIAttributeKind
    value: str

class InputOfProjectCOIAttributeInputSchema(TypedDict):
    project: str
    kind: InputOfProjectCOIAttributeKind
    value: str

ProjectCOIAttributeKind = Literal['institution', 'domain']

InputOfProjectCOIAttributeKind = Literal['institution', 'domain']

class ProjectCreateInputSchema(TypedDict):
    name: str
    description: NotRequired[str]
    team: NotRequired[str | None]
    track: NotRequired[str | None]

class InputOfProjectCreateInputSchema(TypedDict):
    name: str
    description: NotRequired[str]
    team: NotRequired[str | None]
    track: NotRequired[str | None]

class ProjectMembership(TypedDict):
    user: str
    role: ProjectMembershipRoleEnum
    joined_at: str

class InputOfProjectMembership(TypedDict):
    role: InputOfProjectMembershipRoleEnum

ProjectMembershipRoleEnum = Literal['owner', 'contributor']

InputOfProjectMembershipRoleEnum = Literal['owner', 'contributor']

class ProjectRecordInput(TypedDict):
    project: str

class InputOfProjectRecordInput(TypedDict):
    project: str

class ProvenanceAwardSchema(TypedDict):
    award: str
    name: str
    winner: str
    rank_at_selection: int | None
    override_reason: str
    published: bool

class InputOfProvenanceAwardSchema(TypedDict):
    award: str
    name: str
    winner: str
    rank_at_selection: int | None
    override_reason: str
    published: bool

class ProvenanceBallotSchema(TypedDict):
    ballot: str
    judge: str
    rubric_version: str
    responses: list[ProvenanceCriterionSchema]
    weighted_score: float
    judge_effect: float
    adjusted_score: float
    submitted_at: str

class InputOfProvenanceBallotSchema(TypedDict):
    ballot: str
    judge: str
    rubric_version: str
    responses: list[InputOfProvenanceCriterionSchema]
    weighted_score: float
    judge_effect: float
    adjusted_score: float
    submitted_at: str

class ProvenanceCriterionSchema(TypedDict):
    criterion_id: str
    criterion_name: str
    weight: float
    score: float

class InputOfProvenanceCriterionSchema(TypedDict):
    criterion_id: str
    criterion_name: str
    weight: float
    score: float

class ProvenanceSchema(TypedDict):
    project: str
    project_name: str
    rank: int
    raw_score: float | None
    final_score: float
    tie_break: int | None
    normalization_run: str
    ridge_lambda: float
    converged: bool
    grand_mean: float
    ballot_snapshot_available: bool
    ballots: list[ProvenanceBallotSchema] | None
    awards: list[ProvenanceAwardSchema]

class InputOfProvenanceSchema(TypedDict):
    project: str
    project_name: str
    rank: int
    raw_score: float | None
    final_score: float
    tie_break: int | None
    normalization_run: str
    ridge_lambda: float
    converged: bool
    grand_mean: float
    ballot_snapshot_available: bool
    ballots: list[InputOfProvenanceBallotSchema] | None
    awards: list[InputOfProvenanceAwardSchema]

class PublicAnnouncementOutput(TypedDict):
    public_id: str
    title: str
    body: str
    created_at: str

class InputOfPublicAnnouncementOutput(TypedDict):
    pass

class PublicAwardOutput(TypedDict):
    public_id: str
    name: str
    description: str
    eligibility_track: str | None
    require_finalized_submission: bool
    selection_source: str
    evaluation_plan: str | None
    winner_count: int
    allow_stacking: bool
    conflict_group: str
    published_at: str | None
    components: list[ComponentOutput]
    winners: list[PublicWinnerOutput]

class InputOfPublicAwardOutput(TypedDict):
    public_id: str
    name: str
    description: str
    eligibility_track: str | None
    require_finalized_submission: bool
    selection_source: str
    evaluation_plan: str | None
    winner_count: int
    allow_stacking: bool
    conflict_group: str
    published_at: str | None
    components: list[InputOfComponentOutput]
    winners: list[InputOfPublicWinnerOutput]

class PublicEventSchema(TypedDict):
    public_id: str
    name: str
    slug: str
    description: str
    timezone: str
    starts_at: str | None
    ends_at: str | None
    status: str
    tracks: list[Track]
    base_prizes: list[BasePrize]

class InputOfPublicEventSchema(TypedDict):
    public_id: str
    name: str
    slug: str
    description: str
    timezone: str
    starts_at: str | None
    ends_at: str | None
    status: str
    tracks: list[InputOfTrack]
    base_prizes: list[InputOfBasePrize]

class PublicWinnerOutput(TypedDict):
    project: str
    project_name: str

class InputOfPublicWinnerOutput(TypedDict):
    project: str
    project_name: str

class PublicationInput(TypedDict):
    opens_at: str
    closes_at: NotRequired[str | None]
    finalist_stage: NotRequired[str | None]

class InputOfPublicationInput(TypedDict):
    opens_at: str
    closes_at: NotRequired[str | None]
    finalist_stage: NotRequired[str | None]

class PublicationOutput(TypedDict):
    surface: SurfaceEnum
    opens_at: str
    closes_at: str | None
    finalist_stage: str | None
    updated_at: str

class InputOfPublicationOutput(TypedDict):
    opens_at: str
    closes_at: str | None
    finalist_stage: str | None

class QualifierEntryInput(TypedDict):
    external_ref: str
    project: NotRequired[str | None]

class InputOfQualifierEntryInput(TypedDict):
    external_ref: str
    project: NotRequired[str | None]

class QualifierEntryOutput(TypedDict):
    external_ref: str
    project: str
    advanced: bool

class InputOfQualifierEntryOutput(TypedDict):
    external_ref: str
    project: str
    advanced: bool

class QualifierImportInput(TypedDict):
    entries: list[QualifierEntryInput]

class InputOfQualifierImportInput(TypedDict):
    entries: list[InputOfQualifierEntryInput]

class QualifierImportOutput(TypedDict):
    public_id: str
    stage: str
    entries: list[QualifierEntryOutput]
    advanced_count: int
    created_at: str

class InputOfQualifierImportOutput(TypedDict):
    public_id: str
    stage: str
    entries: list[InputOfQualifierEntryOutput]
    advanced_count: int
    created_at: str

class QuestionInput(TypedDict):
    question: str

class InputOfQuestionInput(TypedDict):
    question: str

class QuestionOutput(TypedDict):
    public_id: str
    question: str
    answer: str
    status: EventQuestionStatus
    version: int
    created_at: str
    updated_at: str

class InputOfQuestionOutput(TypedDict):
    pass

class QuestionReviewInput(TypedDict):
    version: int
    status: EventQuestionStatus
    answer: NotRequired[str]
    note: str

class InputOfQuestionReviewInput(TypedDict):
    version: int
    status: InputOfEventQuestionStatus
    answer: NotRequired[str]
    note: str

class RankedResultSchema(TypedDict):
    rank: int
    project: str | None
    project_name: str | None
    raw_score: float | None
    final_score: float
    tie_break: int | None

class InputOfRankedResultSchema(TypedDict):
    rank: int
    project: str | None
    project_name: str | None
    raw_score: float | None
    final_score: float
    tie_break: int | None

class RecordOutput(TypedDict):
    token: str
    claims: dict[str, Any]

class InputOfRecordOutput(TypedDict):
    token: str
    claims: dict[str, Any]

class RedeemInviteInput(TypedDict):
    token: str

class InputOfRedeemInviteInput(TypedDict):
    token: str

class RegistrationInviteCode(TypedDict):
    public_id: str
    code: str
    max_uses: NotRequired[int]
    use_count: int
    created_at: str
    revoked_at: str | None

class InputOfRegistrationInviteCode(TypedDict):
    max_uses: NotRequired[int]

class RegistrationSettings(TypedDict):
    mode: NotRequired[RegistrationSettingsModeEnum]
    capacity: NotRequired[int | None]
    waitlist_enabled: NotRequired[bool]
    updated_at: str

class InputOfRegistrationSettings(TypedDict):
    mode: NotRequired[InputOfRegistrationSettingsModeEnum]
    capacity: NotRequired[int | None]
    waitlist_enabled: NotRequired[bool]

RegistrationSettingsModeEnum = Literal['open', 'application', 'invite_only']

InputOfRegistrationSettingsModeEnum = Literal['open', 'application', 'invite_only']

class ReminderInputSchema(TypedDict):
    kind: ReminderInputSchemaKindEnum
    due_at: str
    audience_kind: str
    audience_params: NotRequired[dict[str, str]]
    subject: str
    body: str

class InputOfReminderInputSchema(TypedDict):
    kind: InputOfReminderInputSchemaKindEnum
    due_at: str
    audience_kind: str
    audience_params: NotRequired[dict[str, str]]
    subject: str
    body: str

ReminderInputSchemaKindEnum = Literal['deadline', 'judging', 'voting']

InputOfReminderInputSchemaKindEnum = Literal['deadline', 'judging', 'voting']

class ReminderSchema(TypedDict):
    public_id: str
    kind: str
    due_at: str
    audience_kind: str
    audience_params: Any
    subject: str
    body: str
    status: str
    sent_message: str | None
    cancelled_at: str | None
    last_error: str

class InputOfReminderSchema(TypedDict):
    public_id: str
    kind: str
    due_at: str
    audience_kind: str
    audience_params: Any
    subject: str
    body: str
    status: str
    sent_message: str | None
    cancelled_at: str | None
    last_error: str

class ResolutionInputSchema(TypedDict):
    resolution_note: str

class InputOfResolutionInputSchema(TypedDict):
    resolution_note: str

class RespondInput(TypedDict):
    response: str

class InputOfRespondInput(TypedDict):
    response: str

class ResultsPublishInputSchema(TypedDict):
    normalization_run: str
    tie_breaks: NotRequired[dict[str, int]]

class InputOfResultsPublishInputSchema(TypedDict):
    normalization_run: str
    tie_breaks: NotRequired[dict[str, int]]

class RetentionPolicyInput(TypedDict):
    participant_data_days: int | None
    private_artifact_days: int | None

class InputOfRetentionPolicyInput(TypedDict):
    participant_data_days: int | None
    private_artifact_days: int | None

class RetentionPolicyOutput(TypedDict):
    participant_data_days: int | None
    private_artifact_days: int | None
    updated_at: str | None

class InputOfRetentionPolicyOutput(TypedDict):
    participant_data_days: int | None
    private_artifact_days: int | None
    updated_at: str | None

class ReviewOutput(TypedDict):
    project: str
    status: str
    decision_note: str
    revision: int
    decided_at: str | None
    findings: list[FindingOutput]

class InputOfReviewOutput(TypedDict):
    project: str
    status: str
    decision_note: str
    revision: int
    decided_at: str | None
    findings: list[InputOfFindingOutput]

class ReviewSummaryOutput(TypedDict):
    project: str
    project_name: str
    status: str
    open_findings: int
    addressed_findings: int
    revision: int

class InputOfReviewSummaryOutput(TypedDict):
    project: str
    project_name: str
    status: str
    open_findings: int
    addressed_findings: int
    revision: int

class RoomOutput(TypedDict):
    public_id: str
    status: str
    quorum: int
    notes: list[dict[str, Any]]
    stances: list[dict[str, Any]]
    tally: list[dict[str, Any]]
    finalization: dict[str, Any]

class InputOfRoomOutput(TypedDict):
    public_id: str
    status: str
    quorum: int
    notes: list[dict[str, Any]]
    stances: list[dict[str, Any]]
    tally: list[dict[str, Any]]
    finalization: dict[str, Any]

class RubricLabCriterionSchema(TypedDict):
    criterion_id: str
    name: str
    weight_share: float
    response_count: int
    missing_count: int
    mean: float | None
    variance: float | None
    scale_use: float | None
    at_min_count: int
    at_max_count: int
    spread_share: float | None
    dominates: bool
    weight_scenarios: list[RubricLabScenarioSchema]

class InputOfRubricLabCriterionSchema(TypedDict):
    criterion_id: str
    name: str
    weight_share: float
    response_count: int
    missing_count: int
    mean: float | None
    variance: float | None
    scale_use: float | None
    at_min_count: int
    at_max_count: int
    spread_share: float | None
    dominates: bool
    weight_scenarios: list[InputOfRubricLabScenarioSchema]

class RubricLabInputSchema(TypedDict):
    rubric_version: NotRequired[str]
    factors: NotRequired[list[float]]

class InputOfRubricLabInputSchema(TypedDict):
    rubric_version: NotRequired[str]
    factors: NotRequired[list[float]]

class RubricLabScenarioSchema(TypedDict):
    factor: float
    order: list[str]
    rank_changed_count: int
    top_changed: bool

class InputOfRubricLabScenarioSchema(TypedDict):
    factor: float
    order: list[str]
    rank_changed_count: int
    top_changed: bool

class RubricLabSchema(TypedDict):
    rubric_version: str
    ballot_count: int
    baseline: list[str]
    criteria: list[RubricLabCriterionSchema]

class InputOfRubricLabSchema(TypedDict):
    rubric_version: str
    ballot_count: int
    baseline: list[str]
    criteria: list[InputOfRubricLabCriterionSchema]

class RubricVersion(TypedDict):
    public_id: str
    number: int
    criteria: Any
    published_at: str

class InputOfRubricVersion(TypedDict):
    number: int
    criteria: Any

class RulesInput(TypedDict):
    min_team_size: int | None
    max_team_size: int | None
    required_artifact_kinds: list[str]
    require_finalized_submission: bool
    require_track: bool
    require_clearance: bool

class InputOfRulesInput(TypedDict):
    min_team_size: int | None
    max_team_size: int | None
    required_artifact_kinds: list[str]
    require_finalized_submission: bool
    require_track: bool
    require_clearance: bool

class RulesOutput(TypedDict):
    min_team_size: int | None
    max_team_size: int | None
    required_artifact_kinds: list[str]
    require_finalized_submission: bool
    require_track: bool
    require_clearance: bool
    updated_at: str | None

class InputOfRulesOutput(TypedDict):
    min_team_size: int | None
    max_team_size: int | None
    required_artifact_kinds: list[str]
    require_finalized_submission: bool
    require_track: bool
    require_clearance: bool
    updated_at: str | None

class SavedSearchInput(TypedDict):
    name: str
    filters: SearchFilters

class InputOfSavedSearchInput(TypedDict):
    name: str
    filters: InputOfSearchFilters

class SavedSearchOutput(TypedDict):
    public_id: str
    name: str
    filters: Any
    created_at: str

class InputOfSavedSearchOutput(TypedDict):
    pass

class ScanInput(TypedDict):
    token: str

class InputOfScanInput(TypedDict):
    token: str

class SearchFilters(TypedDict):
    q: NotRequired[str]
    tags: NotRequired[list[str]]
    artifact_kind: NotRequired[ArtifactKindEnum]
    track: NotRequired[str]
    stage: NotRequired[str]

class InputOfSearchFilters(TypedDict):
    q: NotRequired[str]
    tags: NotRequired[list[str]]
    artifact_kind: NotRequired[InputOfArtifactKindEnum]
    track: NotRequired[str]
    stage: NotRequired[str]

class SearchItemOutput(TypedDict):
    public_id: str
    name: str
    description: str
    track: str | None
    team: str | None
    url: str
    tags: list[str]
    artifact_kinds: list[str]

class InputOfSearchItemOutput(TypedDict):
    public_id: str
    name: str
    description: str
    track: str | None
    team: str | None
    url: str
    tags: list[str]
    artifact_kinds: list[str]

class SearchOutput(TypedDict):
    count: int
    next_offset: int | None
    items: list[SearchItemOutput]

class InputOfSearchOutput(TypedDict):
    count: int
    next_offset: int | None
    items: list[InputOfSearchItemOutput]

SelectionSourceEnum = Literal['manual', 'evaluation', 'community']

InputOfSelectionSourceEnum = Literal['manual', 'evaluation', 'community']

class SensitivityInputSchema(TypedDict):
    ridge_lambdas: NotRequired[list[float]]
    holdout_counts: NotRequired[list[int]]

class InputOfSensitivityInputSchema(TypedDict):
    ridge_lambdas: NotRequired[list[float]]
    holdout_counts: NotRequired[list[int]]

SeverityEnum = Literal['blocking', 'advisory']

InputOfSeverityEnum = Literal['blocking', 'advisory']

class SignedArchiveImportInput(TypedDict):
    name: str
    slug: str
    envelope: Any

class InputOfSignedArchiveImportInput(TypedDict):
    name: str
    slug: str
    envelope: Any

class SignedArchiveOutput(TypedDict):
    manifest: dict[str, Any]
    archive: dict[str, Any]
    public_key_pem: str
    signature: str

class InputOfSignedArchiveOutput(TypedDict):
    manifest: dict[str, Any]
    archive: dict[str, Any]
    public_key_pem: str
    signature: str

class SponsorProjectSchema(TypedDict):
    public_id: str
    name: str
    team_name: str | None
    track_name: str | None

class InputOfSponsorProjectSchema(TypedDict):
    public_id: str
    name: str
    team_name: str | None
    track_name: str | None

class Stage(TypedDict):
    public_id: str
    name: str
    position: NotRequired[int]
    is_initial: NotRequired[bool]
    participation_mode: NotRequired[ParticipationModeEnum]
    created_at: str

class InputOfStage(TypedDict):
    name: str
    position: NotRequired[int]
    is_initial: NotRequired[bool]
    participation_mode: NotRequired[InputOfParticipationModeEnum]

class StageTransition(TypedDict):
    public_id: str
    from_stage: str
    to_stage: str
    created_at: str

class InputOfStageTransition(TypedDict):
    from_stage: str
    to_stage: str

StanceEnum = Literal['endorse', 'object', 'abstain']

InputOfStanceEnum = Literal['endorse', 'object', 'abstain']

class StanceInput(TypedDict):
    stance: StanceEnum
    rationale: NotRequired[str]

class InputOfStanceInput(TypedDict):
    stance: InputOfStanceEnum
    rationale: NotRequired[str]

class SubjectExportOutput(TypedDict):
    subject: dict[str, Any]
    event: str
    data: dict[str, Any]
    retained_data: dict[str, Any]
    artifacts: list[dict[str, Any]]

class InputOfSubjectExportOutput(TypedDict):
    subject: dict[str, Any]
    event: str
    data: dict[str, Any]
    retained_data: dict[str, Any]
    artifacts: list[dict[str, Any]]

class SubjectInput(TypedDict):
    type: TaxonomySubjectType
    id: NotRequired[str]

class InputOfSubjectInput(TypedDict):
    type: InputOfTaxonomySubjectType
    id: NotRequired[str]

SubjectKindEnum = Literal['role', 'user']

InputOfSubjectKindEnum = Literal['role', 'user']

SubjectTypeEnum = Literal['project', 'team']

InputOfSubjectTypeEnum = Literal['project', 'team']

class SubmissionDiffSchema(TypedDict):
    from_version: int
    to_version: int
    diff: Any

class InputOfSubmissionDiffSchema(TypedDict):
    from_version: int
    to_version: int
    diff: Any

class SubmissionDraftInputSchema(TypedDict):
    draft_payload: Any
    draft_revision: int

class InputOfSubmissionDraftInputSchema(TypedDict):
    draft_payload: Any
    draft_revision: int

class SubmissionFinalizeInputSchema(TypedDict):
    draft_revision: int

class InputOfSubmissionFinalizeInputSchema(TypedDict):
    draft_revision: int

class SubmissionReceiptSchema(TypedDict):
    submission: SubmissionSchema
    receipt: str

class InputOfSubmissionReceiptSchema(TypedDict):
    submission: InputOfSubmissionSchema
    receipt: str

class SubmissionReopenInputSchema(TypedDict):
    reason: NotRequired[str]

class InputOfSubmissionReopenInputSchema(TypedDict):
    reason: NotRequired[str]

class SubmissionSchema(TypedDict):
    public_id: str
    stage: str
    status: str
    draft_payload: Any
    draft_revision: int
    current_version: str | None
    versions: list[SubmissionVersionSchema]

class InputOfSubmissionSchema(TypedDict):
    public_id: str
    stage: str
    status: str
    draft_payload: Any
    draft_revision: int
    current_version: str | None
    versions: list[InputOfSubmissionVersionSchema]

class SubmissionStageSchema(TypedDict):
    public_id: str
    name: str
    submission: SubmissionSchema | None

class InputOfSubmissionStageSchema(TypedDict):
    public_id: str
    name: str
    submission: InputOfSubmissionSchema | None

class SubmissionVersionSchema(TypedDict):
    public_id: str
    number: int
    digest: str
    finalized_at: str
    finalized_by: str

class InputOfSubmissionVersionSchema(TypedDict):
    public_id: str
    number: int
    digest: str
    finalized_at: str
    finalized_by: str

class SubscriptionInput(TypedDict):
    url: str
    event_types: list[str]
    event: NotRequired[str | None]
    platform: NotRequired[PlatformEnum]

class InputOfSubscriptionInput(TypedDict):
    url: str
    event_types: list[str]
    event: NotRequired[str | None]
    platform: NotRequired[InputOfPlatformEnum]

class SubscriptionIssued(TypedDict):
    public_id: str
    url: str
    event_types: list[str]
    event: str | None
    platform: str
    enabled: bool
    created_at: str
    secret: str

class InputOfSubscriptionIssued(TypedDict):
    public_id: str
    url: str
    event_types: list[str]
    event: str | None
    platform: str
    enabled: bool
    created_at: str
    secret: str

class SubscriptionOutput(TypedDict):
    public_id: str
    url: str
    event_types: list[str]
    event: str | None
    platform: str
    enabled: bool
    created_at: str

class InputOfSubscriptionOutput(TypedDict):
    public_id: str
    url: str
    event_types: list[str]
    event: str | None
    platform: str
    enabled: bool
    created_at: str

SurfaceEnum = Literal['gallery', 'finalists', 'feedback', 'winners', 'archive']

InputOfSurfaceEnum = Literal['gallery', 'finalists', 'feedback', 'winners', 'archive']

class TagInput(TypedDict):
    tags: list[str]

class InputOfTagInput(TypedDict):
    tags: list[str]

class TaxonomyCreateInput(TypedDict):
    key: str
    name: str
    applies_to: TaxonomySubjectType
    allows_multiple: NotRequired[bool]
    terms: NotRequired[list[TermInput]]

class InputOfTaxonomyCreateInput(TypedDict):
    key: str
    name: str
    applies_to: InputOfTaxonomySubjectType
    allows_multiple: NotRequired[bool]
    terms: NotRequired[list[InputOfTermInput]]

class TaxonomyOutput(TypedDict):
    public_id: str
    key: str
    name: str
    applies_to: str
    allows_multiple: bool
    terms: list[TermOutput]

class InputOfTaxonomyOutput(TypedDict):
    public_id: str
    key: str
    name: str
    applies_to: str
    allows_multiple: bool
    terms: list[InputOfTermOutput]

TaxonomySubjectType = Literal['project', 'person', 'event']

InputOfTaxonomySubjectType = Literal['project', 'person', 'event']

class Team(TypedDict):
    public_id: str
    name: str
    created_at: str
    members: list[TeamMembership]

class InputOfTeam(TypedDict):
    name: str

class TeamInvite(TypedDict):
    public_id: str
    token: str
    created_at: str
    expires_at: str | None
    max_uses: int
    use_count: int
    revoked_at: str | None

class InputOfTeamInvite(TypedDict):
    pass

class TeamMembership(TypedDict):
    user_public_id: str
    username: str
    role: NotRequired[TeamMembershipRoleEnum]
    joined_at: str

class InputOfTeamMembership(TypedDict):
    role: NotRequired[InputOfTeamMembershipRoleEnum]

TeamMembershipRoleEnum = Literal['member', 'captain']

InputOfTeamMembershipRoleEnum = Literal['member', 'captain']

class TeamOpeningInput(TypedDict):
    title: str
    description: NotRequired[str]
    desired_skills: list[str]
    desired_roles: NotRequired[list[str]]
    interests: NotRequired[list[str]]
    min_availability_hours_per_week: NotRequired[int | None]
    project: NotRequired[str | None]
    is_open: NotRequired[bool]

class InputOfTeamOpeningInput(TypedDict):
    title: str
    description: NotRequired[str]
    desired_skills: list[str]
    desired_roles: NotRequired[list[str]]
    interests: NotRequired[list[str]]
    min_availability_hours_per_week: NotRequired[int | None]
    project: NotRequired[str | None]
    is_open: NotRequired[bool]

class TeamOpeningSchema(TypedDict):
    public_id: str
    team: str
    team_name: str
    project: str | None
    project_name: str | None
    title: str
    description: str
    desired_skills: list[str]
    desired_roles: list[str]
    interests: list[str]
    min_availability_hours_per_week: int | None
    is_open: bool
    matched_skills: list[str]
    matched_roles: NotRequired[list[str]]
    matched_interests: NotRequired[list[str]]
    availability_compatible: NotRequired[bool | None]

class InputOfTeamOpeningSchema(TypedDict):
    public_id: str
    team: str
    team_name: str
    project: str | None
    project_name: str | None
    title: str
    description: str
    desired_skills: list[str]
    desired_roles: list[str]
    interests: list[str]
    min_availability_hours_per_week: int | None
    is_open: bool
    matched_skills: list[str]
    matched_roles: NotRequired[list[str]]
    matched_interests: NotRequired[list[str]]
    availability_compatible: NotRequired[bool | None]

class TemporalGate(TypedDict):
    public_id: str
    name: str
    opens_at: NotRequired[str | None]
    closes_at: NotRequired[str | None]
    event_local_opens_at: str | None
    event_local_closes_at: str | None
    dst_warning: str | None
    created_at: str

class InputOfTemporalGate(TypedDict):
    name: str
    opens_at: NotRequired[str | None]
    closes_at: NotRequired[str | None]

class TermInput(TypedDict):
    key: str
    label: str

class InputOfTermInput(TypedDict):
    key: str
    label: str

class TermOutput(TypedDict):
    key: str
    label: str
    position: int

class InputOfTermOutput(TypedDict):
    key: str
    label: str
    position: int

ThemeEnum = Literal['default', 'dark', 'minimal']

InputOfThemeEnum = Literal['default', 'dark', 'minimal']

class TimelineWindowSchema(TypedDict):
    label: str
    opens_at: str | None
    closes_at: str | None
    event_local_opens_at: str | None
    event_local_closes_at: str | None
    dst_warning: str | None

class InputOfTimelineWindowSchema(TypedDict):
    label: str
    opens_at: str | None
    closes_at: str | None
    event_local_opens_at: str | None
    event_local_closes_at: str | None
    dst_warning: str | None

class Track(TypedDict):
    public_id: str
    name: str
    description: NotRequired[str]
    position: NotRequired[int]

class InputOfTrack(TypedDict):
    name: str
    description: NotRequired[str]
    position: NotRequired[int]

class TransferCaptainInput(TypedDict):
    user: str

class InputOfTransferCaptainInput(TypedDict):
    user: str

class UploadCompleteInputSchema(TypedDict):
    parts: NotRequired[Any]

class InputOfUploadCompleteInputSchema(TypedDict):
    parts: NotRequired[Any]

class UploadIntentInputSchema(TypedDict):
    kind: str
    visibility: str
    title: NotRequired[str]
    byte_size: int
    content_type: str

class InputOfUploadIntentInputSchema(TypedDict):
    kind: str
    visibility: str
    title: NotRequired[str]
    byte_size: int
    content_type: str

class UploadIntentSchema(TypedDict):
    artifact: ArtifactSchema
    intent: str
    expires_at: str
    upload: Any

class InputOfUploadIntentSchema(TypedDict):
    artifact: InputOfArtifactSchema
    intent: str
    expires_at: str
    upload: Any

class UserSummarySchema(TypedDict):
    public_id: str
    username: str
    memberships: list[MembershipSummarySchema]

class InputOfUserSummarySchema(TypedDict):
    public_id: str
    username: str
    memberships: list[InputOfMembershipSummarySchema]

class ValidationSchema(TypedDict):
    outcome: str
    detail: str

class InputOfValidationSchema(TypedDict):
    outcome: str
    detail: str

class VerificationKeyOutput(TypedDict):
    issuer: str
    algorithm: str
    public_key_pem: str

class InputOfVerificationKeyOutput(TypedDict):
    issuer: str
    algorithm: str
    public_key_pem: str

class VerifyRecordInput(TypedDict):
    token: str

class InputOfVerifyRecordInput(TypedDict):
    token: str

class VerifyRecordOutput(TypedDict):
    valid: bool
    claims: NotRequired[dict[str, Any]]
    error: NotRequired[str]

class InputOfVerifyRecordOutput(TypedDict):
    valid: bool
    claims: NotRequired[dict[str, Any]]
    error: NotRequired[str]

class VoteInputSchema(TypedDict):
    project: str
    token: NotRequired[str]

class InputOfVoteInputSchema(TypedDict):
    project: str
    token: NotRequired[str]

class VoteReceiptSchema(TypedDict):
    public_id: str

class InputOfVoteReceiptSchema(TypedDict):
    public_id: str

class VoteToken(TypedDict):
    public_id: str
    token: NotRequired[str]
    redeemed_at: NotRequired[str | None]
    created_at: str

class InputOfVoteToken(TypedDict):
    token: NotRequired[str]
    redeemed_at: NotRequired[str | None]

class VoteTokenBatchInputSchema(TypedDict):
    count: NotRequired[int]

class InputOfVoteTokenBatchInputSchema(TypedDict):
    count: NotRequired[int]

class VotingPlan(TypedDict):
    public_id: str
    identity_mode: NotRequired[IdentityModeEnum]
    opens_at: str
    closes_at: str
    allow_comments: NotRequired[bool]
    comment_visibility: NotRequired[CommentVisibilityEnum]
    results_published_at: str | None
    created_at: str
    updated_at: str

class InputOfVotingPlan(TypedDict):
    identity_mode: NotRequired[InputOfIdentityModeEnum]
    opens_at: str
    closes_at: str
    allow_comments: NotRequired[bool]
    comment_visibility: NotRequired[InputOfCommentVisibilityEnum]

class VotingResultSchema(TypedDict):
    project: str
    name: str
    votes: int

class InputOfVotingResultSchema(TypedDict):
    project: str
    name: str
    votes: int

class VotingStatusSchema(TypedDict):
    identity_mode: str
    opens_at: str
    closes_at: str
    is_open: bool
    allow_comments: bool

class InputOfVotingStatusSchema(TypedDict):
    identity_mode: str
    opens_at: str
    closes_at: str
    is_open: bool
    allow_comments: bool

class WinnerInput(TypedDict):
    project: str
    override_reason: NotRequired[str]

class InputOfWinnerInput(TypedDict):
    project: str
    override_reason: NotRequired[str]

class WinnerOutput(TypedDict):
    public_id: str
    project: str
    project_name: str
    source: str
    evidence: Any
    override_reason: str
    selected_at: str
    fulfillments: list[dict[str, Any]]

class InputOfWinnerOutput(TypedDict):
    public_id: str
    project: str
    project_name: str
    source: str
    evidence: Any
    override_reason: str
    selected_at: str
    fulfillments: list[dict[str, Any]]

class WorkflowPresetInput(TypedDict):
    preset: str

class InputOfWorkflowPresetInput(TypedDict):
    preset: str

class WorkflowPresetResult(TypedDict):
    stages: list[Stage]
    plans: list[EvaluationPlan]

class InputOfWorkflowPresetResult(TypedDict):
    stages: list[InputOfStage]
    plans: list[InputOfEvaluationPlan]

class WorkspaceInputSchema(TypedDict):
    name: str
    slug: NotRequired[str]

class InputOfWorkspaceInputSchema(TypedDict):
    name: str
    slug: NotRequired[str]

class WorkspaceSchema(TypedDict):
    public_id: str
    name: str
    slug: str

class InputOfWorkspaceSchema(TypedDict):
    public_id: str
    name: str
    slug: str

OPERATIONS = {'delete_api_v1_workspaces_workspace_public_id_event_templates_template_public_id': {'method': 'DELETE',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/event-templates/{template_public_id}/',
                                                                                     'path_params': ['template_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id': {'method': 'DELETE',
                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/',
                                                                         'path_params': ['event_public_id',
                                                                                         'workspace_public_id'],
                                                                         'query_params': [],
                                                                         'request_body': False,
                                                                         'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements_announcement_public_id': {'method': 'DELETE',
                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/announcements/{announcement_public_id}/',
                                                                                                              'path_params': ['announcement_public_id',
                                                                                                                              'event_public_id',
                                                                                                                              'workspace_public_id'],
                                                                                                              'query_params': [],
                                                                                                              'request_body': False,
                                                                                                              'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_sponsors_user_public_id': {'method': 'DELETE',
                                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/sponsors/{user_public_id}/',
                                                                                                                        'path_params': ['award_public_id',
                                                                                                                                        'event_public_id',
                                                                                                                                        'user_public_id',
                                                                                                                                        'workspace_public_id'],
                                                                                                                        'query_params': [],
                                                                                                                        'request_body': False,
                                                                                                                        'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes_prize_public_id': {'method': 'DELETE',
                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/{prize_public_id}/',
                                                                                                     'path_params': ['event_public_id',
                                                                                                                     'prize_public_id',
                                                                                                                     'workspace_public_id'],
                                                                                                     'query_params': [],
                                                                                                     'request_body': False,
                                                                                                     'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes_attribute_public_id': {'method': 'DELETE',
                                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-project-attributes/{attribute_public_id}/',
                                                                                                                    'path_params': ['attribute_public_id',
                                                                                                                                    'event_public_id',
                                                                                                                                    'workspace_public_id'],
                                                                                                                    'query_params': [],
                                                                                                                    'request_body': False,
                                                                                                                    'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships_relationship_public_id': {'method': 'DELETE',
                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-relationships/{relationship_public_id}/',
                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                  'relationship_public_id',
                                                                                                                                  'workspace_public_id'],
                                                                                                                  'query_params': [],
                                                                                                                  'request_body': False,
                                                                                                                  'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships_membership_public_id': {'method': 'DELETE',
                                                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/memberships/{membership_public_id}/',
                                                                                                                                          'path_params': ['event_public_id',
                                                                                                                                                          'membership_public_id',
                                                                                                                                                          'pool_public_id',
                                                                                                                                                          'workspace_public_id'],
                                                                                                                                          'query_params': [],
                                                                                                                                          'request_body': False,
                                                                                                                                          'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations_invitation_public_id': {'method': 'DELETE',
                                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-invitations/{invitation_public_id}/',
                                                                                                                'path_params': ['event_public_id',
                                                                                                                                'invitation_public_id',
                                                                                                                                'workspace_public_id'],
                                                                                                                'query_params': [],
                                                                                                                'request_body': False,
                                                                                                                'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_location_public_id': {'method': 'DELETE',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/{location_public_id}/',
                                                                                                      'path_params': ['event_public_id',
                                                                                                                      'location_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': False,
                                                                                                      'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites_invite_public_id': {'method': 'DELETE',
                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/invites/{invite_public_id}/',
                                                                                                          'path_params': ['event_public_id',
                                                                                                                          'invite_public_id',
                                                                                                                          'workspace_public_id'],
                                                                                                          'query_params': [],
                                                                                                          'request_body': False,
                                                                                                          'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_block_public_id': {'method': 'DELETE',
                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/{block_public_id}/',
                                                                                                     'path_params': ['block_public_id',
                                                                                                                     'event_public_id',
                                                                                                                     'workspace_public_id'],
                                                                                                     'query_params': [],
                                                                                                     'request_body': False,
                                                                                                     'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_policies_policy_public_id': {'method': 'DELETE',
                                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/{policy_public_id}/',
                                                                                                   'path_params': ['event_public_id',
                                                                                                                   'policy_public_id',
                                                                                                                   'workspace_public_id'],
                                                                                                   'query_params': [],
                                                                                                   'request_body': False,
                                                                                                   'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings_binding_public_id': {'method': 'DELETE',
                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-bindings/{binding_public_id}/',
                                                                                                           'path_params': ['binding_public_id',
                                                                                                                           'event_public_id',
                                                                                                                           'workspace_public_id'],
                                                                                                           'query_params': [],
                                                                                                           'request_body': False,
                                                                                                           'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules_surface': {'method': 'DELETE',
                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/publication-schedules/{surface}/',
                                                                                                       'path_params': ['event_public_id',
                                                                                                                       'surface',
                                                                                                                       'workspace_public_id'],
                                                                                                       'query_params': ['surface'],
                                                                                                       'request_body': False,
                                                                                                       'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes_code_public_id': {'method': 'DELETE',
                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-invite-codes/{code_public_id}/',
                                                                                                                  'path_params': ['code_public_id',
                                                                                                                                  'event_public_id',
                                                                                                                                  'workspace_public_id'],
                                                                                                                  'query_params': [],
                                                                                                                  'request_body': False,
                                                                                                                  'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches_view_public_id': {'method': 'DELETE',
                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/{view_public_id}/',
                                                                                                       'path_params': ['event_public_id',
                                                                                                                       'view_public_id',
                                                                                                                       'workspace_public_id'],
                                                                                                       'query_params': [],
                                                                                                       'request_body': False,
                                                                                                       'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions_transition_public_id': {'method': 'DELETE',
                                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-transitions/{transition_public_id}/',
                                                                                                                'path_params': ['event_public_id',
                                                                                                                                'transition_public_id',
                                                                                                                                'workspace_public_id'],
                                                                                                                'query_params': [],
                                                                                                                'request_body': False,
                                                                                                                'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id': {'method': 'DELETE',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'stage_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': False,
                                                                                                'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id': {'method': 'DELETE',
                                                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/',
                                                                                                                                'path_params': ['event_public_id',
                                                                                                                                                'plan_public_id',
                                                                                                                                                'stage_public_id',
                                                                                                                                                'workspace_public_id'],
                                                                                                                                'query_params': [],
                                                                                                                                'request_body': False,
                                                                                                                                'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft': {'method': 'DELETE',
                                                                                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/{project_public_id}/draft/',
                                                                                                                                                                'path_params': ['event_public_id',
                                                                                                                                                                                'plan_public_id',
                                                                                                                                                                                'project_public_id',
                                                                                                                                                                                'stage_public_id',
                                                                                                                                                                                'workspace_public_id'],
                                                                                                                                                                'query_params': [],
                                                                                                                                                                'request_body': False,
                                                                                                                                                                'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_timezone_timeline': {'method': 'DELETE',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/timezone-timeline/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks_track_public_id': {'method': 'DELETE',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/{track_public_id}/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'track_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': False,
                                                                                                'response_kind': 'none'},
 'delete_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id': {'method': 'DELETE',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/taxonomies/{taxonomy_public_id}/',
                                                                                'path_params': ['taxonomy_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': False,
                                                                                'response_kind': 'none'},
 'get_api_v1_accounts_me': {'method': 'GET',
                            'path': '/api/v1/accounts/me/',
                            'path_params': [],
                            'query_params': [],
                            'request_body': False,
                            'response_kind': 'json'},
 'get_api_v1_audit_workspace_public_id': {'method': 'GET',
                                          'path': '/api/v1/audit/{workspace_public_id}/',
                                          'path_params': ['workspace_public_id'],
                                          'query_params': [],
                                          'request_body': False,
                                          'response_kind': 'json'},
 'get_api_v1_audit_workspace_public_id_events_event_public_id_config_history': {'method': 'GET',
                                                                                'path': '/api/v1/audit/{workspace_public_id}/events/{event_public_id}/config-history/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': False,
                                                                                'response_kind': 'json'},
 'get_api_v1_events_event_public_id': {'method': 'GET',
                                       'path': '/api/v1/events/{event_public_id}/',
                                       'path_params': ['event_public_id'],
                                       'query_params': [],
                                       'request_body': False,
                                       'response_kind': 'json'},
 'get_api_v1_events_event_public_id_announcements': {'method': 'GET',
                                                     'path': '/api/v1/events/{event_public_id}/announcements/',
                                                     'path_params': ['event_public_id'],
                                                     'query_params': ['offset'],
                                                     'request_body': False,
                                                     'response_kind': 'json'},
 'get_api_v1_events_event_public_id_awards': {'method': 'GET',
                                              'path': '/api/v1/events/{event_public_id}/awards/',
                                              'path_params': ['event_public_id'],
                                              'query_params': [],
                                              'request_body': False,
                                              'response_kind': 'json'},
 'get_api_v1_events_event_public_id_finalists': {'method': 'GET',
                                                 'path': '/api/v1/events/{event_public_id}/finalists/',
                                                 'path_params': ['event_public_id'],
                                                 'query_params': [],
                                                 'request_body': False,
                                                 'response_kind': 'json'},
 'get_api_v1_events_event_public_id_gallery': {'method': 'GET',
                                               'path': '/api/v1/events/{event_public_id}/gallery/',
                                               'path_params': ['event_public_id'],
                                               'query_params': [],
                                               'request_body': False,
                                               'response_kind': 'json'},
 'get_api_v1_events_event_public_id_questions': {'method': 'GET',
                                                 'path': '/api/v1/events/{event_public_id}/questions/',
                                                 'path_params': ['event_public_id'],
                                                 'query_params': ['offset'],
                                                 'request_body': False,
                                                 'response_kind': 'json'},
 'get_api_v1_events_event_public_id_search': {'method': 'GET',
                                              'path': '/api/v1/events/{event_public_id}/search/',
                                              'path_params': ['event_public_id'],
                                              'query_params': ['artifact_kind',
                                                               'offset',
                                                               'q',
                                                               'stage',
                                                               'tags',
                                                               'track'],
                                              'request_body': False,
                                              'response_kind': 'json'},
 'get_api_v1_export_csv': {'method': 'GET',
                           'path': '/api/v1/export.csv',
                           'path_params': [],
                           'query_params': [],
                           'request_body': False,
                           'response_kind': 'text'},
 'get_api_v1_gallery': {'method': 'GET',
                        'path': '/api/v1/gallery/',
                        'path_params': [],
                        'query_params': [],
                        'request_body': False,
                        'response_kind': 'json'},
 'get_api_v1_health': {'method': 'GET',
                       'path': '/api/v1/health/',
                       'path_params': [],
                       'query_params': [],
                       'request_body': False,
                       'response_kind': 'json'},
 'get_api_v1_judge_scores': {'method': 'GET',
                             'path': '/api/v1/judge/scores/',
                             'path_params': [],
                             'query_params': [],
                             'request_body': False,
                             'response_kind': 'json'},
 'get_api_v1_public_events_event_public_id_voting_candidates': {'method': 'GET',
                                                                'path': '/api/v1/public/events/{event_public_id}/voting/candidates/',
                                                                'path_params': ['event_public_id'],
                                                                'query_params': [],
                                                                'request_body': False,
                                                                'response_kind': 'json'},
 'get_api_v1_public_events_event_public_id_voting_results': {'method': 'GET',
                                                             'path': '/api/v1/public/events/{event_public_id}/voting/results/',
                                                             'path_params': ['event_public_id'],
                                                             'query_params': [],
                                                             'request_body': False,
                                                             'response_kind': 'json'},
 'get_api_v1_public_events_event_public_id_voting_status': {'method': 'GET',
                                                            'path': '/api/v1/public/events/{event_public_id}/voting/status/',
                                                            'path_params': ['event_public_id'],
                                                            'query_params': [],
                                                            'request_body': False,
                                                            'response_kind': 'json'},
 'get_api_v1_records_verification_key': {'method': 'GET',
                                         'path': '/api/v1/records/verification-key/',
                                         'path_params': [],
                                         'query_params': [],
                                         'request_body': False,
                                         'response_kind': 'json'},
 'get_api_v1_schema': {'method': 'GET',
                       'path': '/api/v1/schema/',
                       'path_params': [],
                       'query_params': ['format', 'lang'],
                       'request_body': False,
                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_api_credentials': {'method': 'GET',
                                                               'path': '/api/v1/workspaces/{workspace_public_id}/api-credentials/',
                                                               'path_params': ['workspace_public_id'],
                                                               'query_params': [],
                                                               'request_body': False,
                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_event_templates': {'method': 'GET',
                                                               'path': '/api/v1/workspaces/{workspace_public_id}/event-templates/',
                                                               'path_params': ['workspace_public_id'],
                                                               'query_params': [],
                                                               'request_body': False,
                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_event_templates_library': {'method': 'GET',
                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/event-templates/library/',
                                                                       'path_params': ['workspace_public_id'],
                                                                       'query_params': [],
                                                                       'request_body': False,
                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events': {'method': 'GET',
                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/',
                                                      'path_params': ['workspace_public_id'],
                                                      'query_params': [],
                                                      'request_body': False,
                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id': {'method': 'GET',
                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/',
                                                                      'path_params': ['event_public_id',
                                                                                      'workspace_public_id'],
                                                                      'query_params': [],
                                                                      'request_body': False,
                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_accessibility_conformance': {'method': 'GET',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/accessibility-conformance/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': False,
                                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements': {'method': 'GET',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/announcements/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': False,
                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_applications': {'method': 'GET',
                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/applications/',
                                                                                   'path_params': ['event_public_id',
                                                                                                   'workspace_public_id'],
                                                                                   'query_params': [],
                                                                                   'request_body': False,
                                                                                   'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive': {'method': 'GET',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/archive/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': ['mode'],
                                                                              'request_body': False,
                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive_signed': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/archive/signed/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': ['mode'],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_attendance': {'method': 'GET',
                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/attendance/',
                                                                                 'path_params': ['event_public_id',
                                                                                                 'workspace_public_id'],
                                                                                 'query_params': [],
                                                                                 'request_body': False,
                                                                                 'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards': {'method': 'GET',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/',
                                                                             'path_params': ['event_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': False,
                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation': {'method': 'GET',
                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/',
                                                                                                          'path_params': ['award_public_id',
                                                                                                                          'event_public_id',
                                                                                                                          'workspace_public_id'],
                                                                                                          'query_params': [],
                                                                                                          'request_body': False,
                                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_candidates': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/candidates/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_fulfillment_export': {'method': 'GET',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/fulfillment-export/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': ['include_notes',
                                                                                                                 'include_recipients',
                                                                                                                 'state'],
                                                                                                'request_body': False,
                                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_fulfillment_export_csv': {'method': 'GET',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/fulfillment-export.csv',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': ['include_notes',
                                                                                                                     'include_recipients',
                                                                                                                     'state'],
                                                                                                    'request_body': False,
                                                                                                    'response_kind': 'text'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_proposals': {'method': 'GET',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/proposals/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': False,
                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes': {'method': 'GET',
                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/',
                                                                                  'path_params': ['event_public_id',
                                                                                                  'workspace_public_id'],
                                                                                  'query_params': [],
                                                                                  'request_body': False,
                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_check_ins': {'method': 'GET',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/check-ins/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': False,
                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes': {'method': 'GET',
                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-project-attributes/',
                                                                                             'path_params': ['event_public_id',
                                                                                                             'workspace_public_id'],
                                                                                             'query_params': [],
                                                                                             'request_body': False,
                                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-relationships/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_rules': {'method': 'GET',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-rules/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': False,
                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_audiences': {'method': 'GET',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/audiences/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': False,
                                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_messages': {'method': 'GET',
                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/messages/',
                                                                                              'path_params': ['event_public_id',
                                                                                                              'workspace_public_id'],
                                                                                              'query_params': [],
                                                                                              'request_body': False,
                                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions': {'method': 'GET',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/questions/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': ['offset'],
                                                                                               'request_body': False,
                                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders': {'method': 'GET',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/reminders/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': False,
                                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_dashboard': {'method': 'GET',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/dashboard/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': False,
                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_reviews': {'method': 'GET',
                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/eligibility-reviews/',
                                                                                          'path_params': ['event_public_id',
                                                                                                          'workspace_public_id'],
                                                                                          'query_params': ['status'],
                                                                                          'request_body': False,
                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_rules': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/eligibility-rules/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools': {'method': 'GET',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': False,
                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships': {'method': 'GET',
                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/memberships/',
                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                  'pool_public_id',
                                                                                                                                  'workspace_public_id'],
                                                                                                                  'query_params': [],
                                                                                                                  'request_body': False,
                                                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_suggest_judges': {'method': 'GET',
                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/suggest-judges/',
                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                     'pool_public_id',
                                                                                                                                     'workspace_public_id'],
                                                                                                                     'query_params': [],
                                                                                                                     'request_body': False,
                                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_grants': {'method': 'GET',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-grants/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': False,
                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms': {'method': 'GET',
                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/',
                                                                            'path_params': ['event_public_id',
                                                                                            'workspace_public_id'],
                                                                            'query_params': [],
                                                                            'request_body': False,
                                                                            'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'form_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_versions': {'method': 'GET',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/versions/',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'form_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': [],
                                                                                                    'request_body': False,
                                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_calendar': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-calendar/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_conflicts': {'method': 'GET',
                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-conflicts/',
                                                                                      'path_params': ['event_public_id',
                                                                                                      'workspace_public_id'],
                                                                                      'query_params': [],
                                                                                      'request_body': False,
                                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-invitations/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_workload': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-workload/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_locations': {'method': 'GET',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': False,
                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_matches': {'method': 'GET',
                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/matches/',
                                                                                          'path_params': ['event_public_id',
                                                                                                          'workspace_public_id'],
                                                                                          'query_params': [],
                                                                                          'request_body': False,
                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_my_openings': {'method': 'GET',
                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/my-openings/',
                                                                                              'path_params': ['event_public_id',
                                                                                                              'workspace_public_id'],
                                                                                              'query_params': [],
                                                                                              'request_body': False,
                                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings_opening_public_id_matches': {'method': 'GET',
                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/{opening_public_id}/matches/',
                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                     'opening_public_id',
                                                                                                                                     'workspace_public_id'],
                                                                                                                     'query_params': [],
                                                                                                                     'request_body': False,
                                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profile': {'method': 'GET',
                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/profile/',
                                                                                          'path_params': ['event_public_id',
                                                                                                          'workspace_public_id'],
                                                                                          'query_params': [],
                                                                                          'request_body': False,
                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profiles': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/profiles/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_application': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-application/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_attendance': {'method': 'GET',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-attendance/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': False,
                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_pass': {'method': 'GET',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-pass/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': [],
                                                                              'request_body': False,
                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_pass_qr': {'method': 'GET',
                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-pass/qr/',
                                                                                 'path_params': ['event_public_id',
                                                                                                 'workspace_public_id'],
                                                                                 'query_params': [],
                                                                                 'request_body': False,
                                                                                 'response_kind': 'text'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team': {'method': 'GET',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': [],
                                                                              'request_body': False,
                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites': {'method': 'GET',
                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/invites/',
                                                                                      'path_params': ['event_public_id',
                                                                                                      'workspace_public_id'],
                                                                                      'query_params': [],
                                                                                      'request_body': False,
                                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_onsite_summary': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/onsite-summary/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_analytics': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/analytics/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': ['plan_offset'],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_checklist': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/checklist/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation': {'method': 'GET',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/moderation/',
                                                                                            'path_params': ['event_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': ['kind',
                                                                                                             'offset'],
                                                                                            'request_body': False,
                                                                                            'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation_reviews': {'method': 'GET',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/moderation/reviews/',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': ['kind',
                                                                                                                     'offset'],
                                                                                                    'request_body': False,
                                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_summary': {'method': 'GET',
                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/summary/',
                                                                                         'path_params': ['event_public_id',
                                                                                                         'workspace_public_id'],
                                                                                         'query_params': [],
                                                                                         'request_body': False,
                                                                                         'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_page': {'method': 'GET',
                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/',
                                                                           'path_params': ['event_public_id',
                                                                                           'workspace_public_id'],
                                                                           'query_params': [],
                                                                           'request_body': False,
                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_page_accessibility_audit': {'method': 'GET',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/accessibility-audit/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': False,
                                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks': {'method': 'GET',
                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/',
                                                                                  'path_params': ['event_public_id',
                                                                                                  'workspace_public_id'],
                                                                                  'query_params': [],
                                                                                  'request_body': False,
                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_permission_matrix': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/permission-matrix/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_policies': {'method': 'GET',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/',
                                                                               'path_params': ['event_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': False,
                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings': {'method': 'GET',
                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-bindings/',
                                                                                      'path_params': ['event_public_id',
                                                                                                      'workspace_public_id'],
                                                                                      'query_params': [],
                                                                                      'request_body': False,
                                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_presets': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-presets/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_policy': {'method': 'GET',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/retention-policy/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': False,
                                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_project_locations': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/project-locations/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects': {'method': 'GET',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/',
                                                                               'path_params': ['event_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': False,
                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id': {'method': 'GET',
                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/',
                                                                                                 'path_params': ['event_public_id',
                                                                                                                 'project_public_id',
                                                                                                                 'workspace_public_id'],
                                                                                                 'query_params': [],
                                                                                                 'request_body': False,
                                                                                                 'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts': {'method': 'GET',
                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/',
                                                                                                           'path_params': ['event_public_id',
                                                                                                                           'project_public_id',
                                                                                                                           'workspace_public_id'],
                                                                                                           'query_params': [],
                                                                                                           'request_body': False,
                                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id': {'method': 'GET',
                                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/',
                                                                                                                              'path_params': ['artifact_public_id',
                                                                                                                                              'event_public_id',
                                                                                                                                              'project_public_id',
                                                                                                                                              'workspace_public_id'],
                                                                                                                              'query_params': [],
                                                                                                                              'request_body': False,
                                                                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_preflight': {'method': 'GET',
                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/preflight/',
                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                     'project_public_id',
                                                                                                                                     'workspace_public_id'],
                                                                                                                     'query_params': [],
                                                                                                                     'request_body': False,
                                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments': {'method': 'GET',
                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/comments/',
                                                                                                          'path_params': ['event_public_id',
                                                                                                                          'project_public_id',
                                                                                                                          'workspace_public_id'],
                                                                                                          'query_params': [],
                                                                                                          'request_body': False,
                                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility': {'method': 'GET',
                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/',
                                                                                                             'path_params': ['event_public_id',
                                                                                                                             'project_public_id',
                                                                                                                             'workspace_public_id'],
                                                                                                             'query_params': [],
                                                                                                             'request_body': False,
                                                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms': {'method': 'GET',
                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/forms/',
                                                                                                       'path_params': ['event_public_id',
                                                                                                                       'project_public_id',
                                                                                                                       'workspace_public_id'],
                                                                                                       'query_params': [],
                                                                                                       'request_body': False,
                                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms_version_public_id_response': {'method': 'GET',
                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/forms/{version_public_id}/response/',
                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                  'project_public_id',
                                                                                                                                                  'version_public_id',
                                                                                                                                                  'workspace_public_id'],
                                                                                                                                  'query_params': [],
                                                                                                                                  'request_body': False,
                                                                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_notes': {'method': 'GET',
                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/mentor-notes/',
                                                                                                              'path_params': ['event_public_id',
                                                                                                                              'project_public_id',
                                                                                                                              'workspace_public_id'],
                                                                                                              'query_params': [],
                                                                                                              'request_body': False,
                                                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions': {'method': 'GET',
                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/',
                                                                                                             'path_params': ['event_public_id',
                                                                                                                             'project_public_id',
                                                                                                                             'workspace_public_id'],
                                                                                                             'query_params': [],
                                                                                                             'request_body': False,
                                                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id': {'method': 'GET',
                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/',
                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                             'project_public_id',
                                                                                                                                             'stage_public_id',
                                                                                                                                             'workspace_public_id'],
                                                                                                                             'query_params': [],
                                                                                                                             'request_body': False,
                                                                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_diff': {'method': 'GET',
                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/diff/',
                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                  'project_public_id',
                                                                                                                                                  'stage_public_id',
                                                                                                                                                  'workspace_public_id'],
                                                                                                                                  'query_params': [],
                                                                                                                                  'request_body': False,
                                                                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_tags': {'method': 'GET',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/tags/',
                                                                                                      'path_params': ['event_public_id',
                                                                                                                      'project_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': False,
                                                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules': {'method': 'GET',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/publication-schedules/',
                                                                                            'path_params': ['event_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': [],
                                                                                            'request_body': False,
                                                                                            'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes': {'method': 'GET',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-invite-codes/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': False,
                                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_settings': {'method': 'GET',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-settings/',
                                                                                            'path_params': ['event_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': [],
                                                                                            'request_body': False,
                                                                                            'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches_view_public_id': {'method': 'GET',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/{view_public_id}/',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'view_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': ['offset'],
                                                                                                    'request_body': False,
                                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards': {'method': 'GET',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/awards/',
                                                                                            'path_params': ['event_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': [],
                                                                                            'request_body': False,
                                                                                            'response_kind': 'none'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_projects': {'method': 'GET',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-projects/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': False,
                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_evidence': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-evidence/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_graph_validate': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-graph/validate/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-transitions/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages': {'method': 'GET',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/',
                                                                             'path_params': ['event_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': False,
                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_advance': {'method': 'GET',
                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/advance/',
                                                                                                     'path_params': ['event_public_id',
                                                                                                                     'stage_public_id',
                                                                                                                     'workspace_public_id'],
                                                                                                     'query_params': [],
                                                                                                     'request_body': False,
                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans': {'method': 'GET',
                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/',
                                                                                                              'path_params': ['event_public_id',
                                                                                                                              'stage_public_id',
                                                                                                                              'workspace_public_id'],
                                                                                                              'query_params': [],
                                                                                                              'request_body': False,
                                                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id': {'method': 'GET',
                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/',
                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                             'plan_public_id',
                                                                                                                                             'stage_public_id',
                                                                                                                                             'workspace_public_id'],
                                                                                                                             'query_params': [],
                                                                                                                             'request_body': False,
                                                                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_agreement': {'method': 'GET',
                                                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/agreement/',
                                                                                                                                       'path_params': ['event_public_id',
                                                                                                                                                       'plan_public_id',
                                                                                                                                                       'stage_public_id',
                                                                                                                                                       'workspace_public_id'],
                                                                                                                                       'query_params': [],
                                                                                                                                       'request_body': False,
                                                                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals': {'method': 'GET',
                                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/appeals/',
                                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                                     'plan_public_id',
                                                                                                                                                     'stage_public_id',
                                                                                                                                                     'workspace_public_id'],
                                                                                                                                     'query_params': [],
                                                                                                                                     'request_body': False,
                                                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments': {'method': 'GET',
                                                                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/',
                                                                                                                                         'path_params': ['event_public_id',
                                                                                                                                                         'plan_public_id',
                                                                                                                                                         'stage_public_id',
                                                                                                                                                         'workspace_public_id'],
                                                                                                                                         'query_params': [],
                                                                                                                                         'request_body': False,
                                                                                                                                         'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots': {'method': 'GET',
                                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/',
                                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                                     'plan_public_id',
                                                                                                                                                     'stage_public_id',
                                                                                                                                                     'workspace_public_id'],
                                                                                                                                     'query_params': [],
                                                                                                                                     'request_body': False,
                                                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft': {'method': 'GET',
                                                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/{project_public_id}/draft/',
                                                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                                                             'plan_public_id',
                                                                                                                                                                             'project_public_id',
                                                                                                                                                                             'stage_public_id',
                                                                                                                                                                             'workspace_public_id'],
                                                                                                                                                             'query_params': [],
                                                                                                                                                             'request_body': False,
                                                                                                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_ballots': {'method': 'GET',
                                                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/ballots/',
                                                                                                                                                 'path_params': ['event_public_id',
                                                                                                                                                                 'plan_public_id',
                                                                                                                                                                 'stage_public_id',
                                                                                                                                                                 'workspace_public_id'],
                                                                                                                                                 'query_params': [],
                                                                                                                                                 'request_body': False,
                                                                                                                                                 'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_projects': {'method': 'GET',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration-projects/',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': False,
                                                                                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_status': {'method': 'GET',
                                                                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/status/',
                                                                                                                                                'path_params': ['event_public_id',
                                                                                                                                                                'plan_public_id',
                                                                                                                                                                'stage_public_id',
                                                                                                                                                                'workspace_public_id'],
                                                                                                                                                'query_params': [],
                                                                                                                                                'request_body': False,
                                                                                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_summary': {'method': 'GET',
                                                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/summary/',
                                                                                                                                                 'path_params': ['event_public_id',
                                                                                                                                                                 'plan_public_id',
                                                                                                                                                                 'stage_public_id',
                                                                                                                                                                 'workspace_public_id'],
                                                                                                                                                 'query_params': [],
                                                                                                                                                 'request_body': False,
                                                                                                                                                 'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_candidates': {'method': 'GET',
                                                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/candidates/',
                                                                                                                                        'path_params': ['event_public_id',
                                                                                                                                                        'plan_public_id',
                                                                                                                                                        'stage_public_id',
                                                                                                                                                        'workspace_public_id'],
                                                                                                                                        'query_params': [],
                                                                                                                                        'request_body': False,
                                                                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_close_calls': {'method': 'GET',
                                                                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/close-calls/',
                                                                                                                                         'path_params': ['event_public_id',
                                                                                                                                                         'plan_public_id',
                                                                                                                                                         'stage_public_id',
                                                                                                                                                         'workspace_public_id'],
                                                                                                                                         'query_params': [],
                                                                                                                                         'request_body': False,
                                                                                                                                         'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_feedback_project_public_id': {'method': 'GET',
                                                                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/feedback/{project_public_id}/',
                                                                                                                                                        'path_params': ['event_public_id',
                                                                                                                                                                        'plan_public_id',
                                                                                                                                                                        'project_public_id',
                                                                                                                                                                        'stage_public_id',
                                                                                                                                                                        'workspace_public_id'],
                                                                                                                                                        'query_params': [],
                                                                                                                                                        'request_body': False,
                                                                                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_route': {'method': 'GET',
                                                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/my-route/',
                                                                                                                                      'path_params': ['event_public_id',
                                                                                                                                                      'plan_public_id',
                                                                                                                                                      'stage_public_id',
                                                                                                                                                      'workspace_public_id'],
                                                                                                                                      'query_params': ['remaining_only',
                                                                                                                                                       'start'],
                                                                                                                                      'request_body': False,
                                                                                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_normalization_runs': {'method': 'GET',
                                                                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/normalization-runs/',
                                                                                                                                                'path_params': ['event_public_id',
                                                                                                                                                                'plan_public_id',
                                                                                                                                                                'stage_public_id',
                                                                                                                                                                'workspace_public_id'],
                                                                                                                                                'query_params': [],
                                                                                                                                                'request_body': False,
                                                                                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_comparisons': {'method': 'GET',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/comparisons/',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': False,
                                                                                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_next': {'method': 'GET',
                                                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/next/',
                                                                                                                                           'path_params': ['event_public_id',
                                                                                                                                                           'plan_public_id',
                                                                                                                                                           'stage_public_id',
                                                                                                                                                           'workspace_public_id'],
                                                                                                                                           'query_params': [],
                                                                                                                                           'request_body': False,
                                                                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_results': {'method': 'GET',
                                                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/results/',
                                                                                                                                              'path_params': ['event_public_id',
                                                                                                                                                              'plan_public_id',
                                                                                                                                                              'stage_public_id',
                                                                                                                                                              'workspace_public_id'],
                                                                                                                                              'query_params': [],
                                                                                                                                              'request_body': False,
                                                                                                                                              'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_results_csv': {'method': 'GET',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/results.csv',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': False,
                                                                                                                                                  'response_kind': 'text'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_runs': {'method': 'GET',
                                                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/runs/',
                                                                                                                                           'path_params': ['event_public_id',
                                                                                                                                                           'plan_public_id',
                                                                                                                                                           'stage_public_id',
                                                                                                                                                           'workspace_public_id'],
                                                                                                                                           'query_params': [],
                                                                                                                                           'request_body': False,
                                                                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_progress': {'method': 'GET',
                                                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/progress/',
                                                                                                                                      'path_params': ['event_public_id',
                                                                                                                                                      'plan_public_id',
                                                                                                                                                      'stage_public_id',
                                                                                                                                                      'workspace_public_id'],
                                                                                                                                      'query_params': [],
                                                                                                                                      'request_body': False,
                                                                                                                                      'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_provenance_project_public_id': {'method': 'GET',
                                                                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/provenance/{project_public_id}/',
                                                                                                                                                          'path_params': ['event_public_id',
                                                                                                                                                                          'plan_public_id',
                                                                                                                                                                          'project_public_id',
                                                                                                                                                                          'stage_public_id',
                                                                                                                                                                          'workspace_public_id'],
                                                                                                                                                          'query_params': [],
                                                                                                                                                          'request_body': False,
                                                                                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_rubric': {'method': 'GET',
                                                                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/publish-rubric/',
                                                                                                                                            'path_params': ['event_public_id',
                                                                                                                                                            'plan_public_id',
                                                                                                                                                            'stage_public_id',
                                                                                                                                                            'workspace_public_id'],
                                                                                                                                            'query_params': [],
                                                                                                                                            'request_body': False,
                                                                                                                                            'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_results': {'method': 'GET',
                                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/results/',
                                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                                     'plan_public_id',
                                                                                                                                                     'stage_public_id',
                                                                                                                                                     'workspace_public_id'],
                                                                                                                                     'query_params': [],
                                                                                                                                     'request_body': False,
                                                                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_results_csv': {'method': 'GET',
                                                                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/results.csv',
                                                                                                                                         'path_params': ['event_public_id',
                                                                                                                                                         'plan_public_id',
                                                                                                                                                         'stage_public_id',
                                                                                                                                                         'workspace_public_id'],
                                                                                                                                         'query_params': [],
                                                                                                                                         'request_body': False,
                                                                                                                                         'response_kind': 'text'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_routes': {'method': 'GET',
                                                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/routes/',
                                                                                                                                    'path_params': ['event_public_id',
                                                                                                                                                    'plan_public_id',
                                                                                                                                                    'stage_public_id',
                                                                                                                                                    'workspace_public_id'],
                                                                                                                                    'query_params': ['remaining_only',
                                                                                                                                                     'start'],
                                                                                                                                    'request_body': False,
                                                                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_external_qualifiers': {'method': 'GET',
                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/external-qualifiers/',
                                                                                                                 'path_params': ['event_public_id',
                                                                                                                                 'stage_public_id',
                                                                                                                                 'workspace_public_id'],
                                                                                                                 'query_params': [],
                                                                                                                 'request_body': False,
                                                                                                                 'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_taxonomy_assignments': {'method': 'GET',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/taxonomy-assignments/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': ['subject_type',
                                                                                                            'taxonomy',
                                                                                                            'term'],
                                                                                           'request_body': False,
                                                                                           'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_timezone_timeline': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/timezone-timeline/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks': {'method': 'GET',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/',
                                                                             'path_params': ['event_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': False,
                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_candidates': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/candidates/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan': {'method': 'GET',
                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/',
                                                                                  'path_params': ['event_public_id',
                                                                                                  'workspace_public_id'],
                                                                                  'query_params': [],
                                                                                  'request_body': False,
                                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_abuse_signals': {'method': 'GET',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/abuse-signals/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': False,
                                                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_audit': {'method': 'GET',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/audit/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': False,
                                                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_tokens': {'method': 'GET',
                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/tokens/',
                                                                                         'path_params': ['event_public_id',
                                                                                                         'workspace_public_id'],
                                                                                         'query_params': [],
                                                                                         'request_body': False,
                                                                                         'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_results': {'method': 'GET',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/results/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_status': {'method': 'GET',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/status/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': False,
                                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_events_event_public_id_workflow_presets': {'method': 'GET',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/workflow-presets/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': False,
                                                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_inbox': {'method': 'GET',
                                                     'path': '/api/v1/workspaces/{workspace_public_id}/inbox/',
                                                     'path_params': ['workspace_public_id'],
                                                     'query_params': [],
                                                     'request_body': False,
                                                     'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_judge_directory': {'method': 'GET',
                                                               'path': '/api/v1/workspaces/{workspace_public_id}/judge-directory/',
                                                               'path_params': ['workspace_public_id'],
                                                               'query_params': [],
                                                               'request_body': False,
                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_judge_events': {'method': 'GET',
                                                            'path': '/api/v1/workspaces/{workspace_public_id}/judge-events/',
                                                            'path_params': ['workspace_public_id'],
                                                            'query_params': [],
                                                            'request_body': False,
                                                            'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_judge_expertise_judge_public_id': {'method': 'GET',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/judge-expertise/{judge_public_id}/',
                                                                               'path_params': ['judge_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': False,
                                                                               'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_members': {'method': 'GET',
                                                       'path': '/api/v1/workspaces/{workspace_public_id}/members/',
                                                       'path_params': ['workspace_public_id'],
                                                       'query_params': [],
                                                       'request_body': False,
                                                       'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_my_judge_expertise': {'method': 'GET',
                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/my-judge-expertise/',
                                                                  'path_params': ['workspace_public_id'],
                                                                  'query_params': [],
                                                                  'request_body': False,
                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_my_judge_invitations': {'method': 'GET',
                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/my-judge-invitations/',
                                                                    'path_params': ['workspace_public_id'],
                                                                    'query_params': [],
                                                                    'request_body': False,
                                                                    'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_operator_console': {'method': 'GET',
                                                                'path': '/api/v1/workspaces/{workspace_public_id}/operator-console/',
                                                                'path_params': ['workspace_public_id'],
                                                                'query_params': [],
                                                                'request_body': False,
                                                                'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_participant_events': {'method': 'GET',
                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/participant-events/',
                                                                  'path_params': ['workspace_public_id'],
                                                                  'query_params': [],
                                                                  'request_body': False,
                                                                  'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_taxonomies': {'method': 'GET',
                                                          'path': '/api/v1/workspaces/{workspace_public_id}/taxonomies/',
                                                          'path_params': ['workspace_public_id'],
                                                          'query_params': [],
                                                          'request_body': False,
                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id': {'method': 'GET',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/taxonomies/{taxonomy_public_id}/',
                                                                             'path_params': ['taxonomy_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': False,
                                                                             'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_webhooks': {'method': 'GET',
                                                        'path': '/api/v1/workspaces/{workspace_public_id}/webhooks/',
                                                        'path_params': ['workspace_public_id'],
                                                        'query_params': [],
                                                        'request_body': False,
                                                        'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries': {'method': 'GET',
                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/deliveries/',
                                                                                          'path_params': ['subscription_public_id',
                                                                                                          'workspace_public_id'],
                                                                                          'query_params': [],
                                                                                          'request_body': False,
                                                                                          'response_kind': 'json'},
 'get_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries_delivery_public_id': {'method': 'GET',
                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/deliveries/{delivery_public_id}/',
                                                                                                             'path_params': ['delivery_public_id',
                                                                                                                             'subscription_public_id',
                                                                                                                             'workspace_public_id'],
                                                                                                             'query_params': [],
                                                                                                             'request_body': False,
                                                                                                             'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id': {'method': 'PATCH',
                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/',
                                                                        'path_params': ['event_public_id',
                                                                                        'workspace_public_id'],
                                                                        'query_params': [],
                                                                        'request_body': True,
                                                                        'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_fulfillments_fulfillment_public_id': {'method': 'PATCH',
                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/fulfillments/{fulfillment_public_id}/',
                                                                                                                                  'path_params': ['award_public_id',
                                                                                                                                                  'event_public_id',
                                                                                                                                                  'fulfillment_public_id',
                                                                                                                                                  'workspace_public_id'],
                                                                                                                                  'query_params': [],
                                                                                                                                  'request_body': True,
                                                                                                                                  'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes_prize_public_id': {'method': 'PATCH',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/{prize_public_id}/',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'prize_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': [],
                                                                                                    'request_body': True,
                                                                                                    'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_location_public_id': {'method': 'PATCH',
                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/{location_public_id}/',
                                                                                                     'path_params': ['event_public_id',
                                                                                                                     'location_public_id',
                                                                                                                     'workspace_public_id'],
                                                                                                     'query_params': [],
                                                                                                     'request_body': True,
                                                                                                     'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings_opening_public_id': {'method': 'PATCH',
                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/{opening_public_id}/',
                                                                                                               'path_params': ['event_public_id',
                                                                                                                               'opening_public_id',
                                                                                                                               'workspace_public_id'],
                                                                                                               'query_params': [],
                                                                                                               'request_body': True,
                                                                                                               'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_page': {'method': 'PATCH',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/',
                                                                             'path_params': ['event_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': True,
                                                                             'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_block_public_id': {'method': 'PATCH',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/{block_public_id}/',
                                                                                                    'path_params': ['block_public_id',
                                                                                                                    'event_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': [],
                                                                                                    'request_body': True,
                                                                                                    'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_policies_policy_public_id': {'method': 'PATCH',
                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/{policy_public_id}/',
                                                                                                  'path_params': ['event_public_id',
                                                                                                                  'policy_public_id',
                                                                                                                  'workspace_public_id'],
                                                                                                  'query_params': [],
                                                                                                  'request_body': True,
                                                                                                  'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id': {'method': 'PATCH',
                                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/',
                                                                                                   'path_params': ['event_public_id',
                                                                                                                   'project_public_id',
                                                                                                                   'workspace_public_id'],
                                                                                                   'query_params': [],
                                                                                                   'request_body': True,
                                                                                                   'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_fulfillments_fulfillment_public_id': {'method': 'PATCH',
                                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/fulfillments/{fulfillment_public_id}/',
                                                                                                                          'path_params': ['event_public_id',
                                                                                                                                          'fulfillment_public_id',
                                                                                                                                          'workspace_public_id'],
                                                                                                                          'query_params': [],
                                                                                                                          'request_body': True,
                                                                                                                          'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id': {'method': 'PATCH',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'stage_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': True,
                                                                                               'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id': {'method': 'PATCH',
                                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/',
                                                                                                                               'path_params': ['event_public_id',
                                                                                                                                               'plan_public_id',
                                                                                                                                               'stage_public_id',
                                                                                                                                               'workspace_public_id'],
                                                                                                                               'query_params': [],
                                                                                                                               'request_body': True,
                                                                                                                               'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates_gate_public_id': {'method': 'PATCH',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/{gate_public_id}/',
                                                                                                      'path_params': ['event_public_id',
                                                                                                                      'gate_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': True,
                                                                                                      'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks_track_public_id': {'method': 'PATCH',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/{track_public_id}/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'track_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': True,
                                                                                               'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan': {'method': 'PATCH',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': True,
                                                                                    'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id': {'method': 'PATCH',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/taxonomies/{taxonomy_public_id}/',
                                                                               'path_params': ['taxonomy_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': True,
                                                                               'response_kind': 'json'},
 'patch_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id': {'method': 'PATCH',
                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/',
                                                                                 'path_params': ['subscription_public_id',
                                                                                                 'workspace_public_id'],
                                                                                 'query_params': [],
                                                                                 'request_body': True,
                                                                                 'response_kind': 'json'},
 'post_api_v1_accounts_login': {'method': 'POST',
                                'path': '/api/v1/accounts/login/',
                                'path_params': [],
                                'query_params': [],
                                'request_body': True,
                                'response_kind': 'json'},
 'post_api_v1_accounts_logout': {'method': 'POST',
                                 'path': '/api/v1/accounts/logout/',
                                 'path_params': [],
                                 'query_params': [],
                                 'request_body': False,
                                 'response_kind': 'none'},
 'post_api_v1_audit_workspace_public_id_events_event_public_id_config_history_audit_event_public_id_restore': {'method': 'POST',
                                                                                                               'path': '/api/v1/audit/{workspace_public_id}/events/{event_public_id}/config-history/{audit_event_public_id}/restore/',
                                                                                                               'path_params': ['audit_event_public_id',
                                                                                                                               'event_public_id',
                                                                                                                               'workspace_public_id'],
                                                                                                               'query_params': [],
                                                                                                               'request_body': False,
                                                                                                               'response_kind': 'json'},
 'post_api_v1_public_events_event_public_id_voting_request_email_token': {'method': 'POST',
                                                                          'path': '/api/v1/public/events/{event_public_id}/voting/request-email-token/',
                                                                          'path_params': ['event_public_id'],
                                                                          'query_params': [],
                                                                          'request_body': True,
                                                                          'response_kind': 'json'},
 'post_api_v1_public_events_event_public_id_voting_votes': {'method': 'POST',
                                                            'path': '/api/v1/public/events/{event_public_id}/voting/votes/',
                                                            'path_params': ['event_public_id'],
                                                            'query_params': [],
                                                            'request_body': True,
                                                            'response_kind': 'json'},
 'post_api_v1_records_verify': {'method': 'POST',
                                'path': '/api/v1/records/verify/',
                                'path_params': [],
                                'query_params': [],
                                'request_body': True,
                                'response_kind': 'json'},
 'post_api_v1_submit': {'method': 'POST',
                        'path': '/api/v1/submit/',
                        'path_params': [],
                        'query_params': [],
                        'request_body': False,
                        'response_kind': 'none'},
 'post_api_v1_workspaces': {'method': 'POST',
                            'path': '/api/v1/workspaces/',
                            'path_params': [],
                            'query_params': [],
                            'request_body': True,
                            'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_api_credentials': {'method': 'POST',
                                                                'path': '/api/v1/workspaces/{workspace_public_id}/api-credentials/',
                                                                'path_params': ['workspace_public_id'],
                                                                'query_params': [],
                                                                'request_body': True,
                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_api_credentials_credential_public_id_revoke': {'method': 'POST',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/api-credentials/{credential_public_id}/revoke/',
                                                                                            'path_params': ['credential_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': [],
                                                                                            'request_body': False,
                                                                                            'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_archive_import': {'method': 'POST',
                                                               'path': '/api/v1/workspaces/{workspace_public_id}/archive/import/',
                                                               'path_params': ['workspace_public_id'],
                                                               'query_params': [],
                                                               'request_body': True,
                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_archive_preview': {'method': 'POST',
                                                                'path': '/api/v1/workspaces/{workspace_public_id}/archive/preview/',
                                                                'path_params': ['workspace_public_id'],
                                                                'query_params': [],
                                                                'request_body': True,
                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_archive_signed_import': {'method': 'POST',
                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/archive/signed/import/',
                                                                      'path_params': ['workspace_public_id'],
                                                                      'query_params': [],
                                                                      'request_body': True,
                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_event_templates': {'method': 'POST',
                                                                'path': '/api/v1/workspaces/{workspace_public_id}/event-templates/',
                                                                'path_params': ['workspace_public_id'],
                                                                'query_params': [],
                                                                'request_body': True,
                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_event_templates_library_template_slug_instantiate': {'method': 'POST',
                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/event-templates/library/{template_slug}/instantiate/',
                                                                                                  'path_params': ['template_slug',
                                                                                                                  'workspace_public_id'],
                                                                                                  'query_params': [],
                                                                                                  'request_body': True,
                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_event_templates_template_public_id_instantiate': {'method': 'POST',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/event-templates/{template_public_id}/instantiate/',
                                                                                               'path_params': ['template_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': True,
                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events': {'method': 'POST',
                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/',
                                                       'path_params': ['workspace_public_id'],
                                                       'query_params': [],
                                                       'request_body': True,
                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements': {'method': 'POST',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/announcements/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': True,
                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_applications_application_public_id_decide': {'method': 'POST',
                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/applications/{application_public_id}/decide/',
                                                                                                                 'path_params': ['application_public_id',
                                                                                                                                 'event_public_id',
                                                                                                                                 'workspace_public_id'],
                                                                                                                 'query_params': [],
                                                                                                                 'request_body': True,
                                                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_authz_dry_run': {'method': 'POST',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/authz-dry-run/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': True,
                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards': {'method': 'POST',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': [],
                                                                              'request_body': True,
                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_components': {'method': 'POST',
                                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/components/',
                                                                                                         'path_params': ['award_public_id',
                                                                                                                         'event_public_id',
                                                                                                                         'workspace_public_id'],
                                                                                                         'query_params': [],
                                                                                                         'request_body': True,
                                                                                                         'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation': {'method': 'POST',
                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/',
                                                                                                           'path_params': ['award_public_id',
                                                                                                                           'event_public_id',
                                                                                                                           'workspace_public_id'],
                                                                                                           'query_params': [],
                                                                                                           'request_body': True,
                                                                                                           'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_close': {'method': 'POST',
                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/close/',
                                                                                                                 'path_params': ['award_public_id',
                                                                                                                                 'event_public_id',
                                                                                                                                 'workspace_public_id'],
                                                                                                                 'query_params': [],
                                                                                                                 'request_body': False,
                                                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_finalize': {'method': 'POST',
                                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/finalize/',
                                                                                                                    'path_params': ['award_public_id',
                                                                                                                                    'event_public_id',
                                                                                                                                    'workspace_public_id'],
                                                                                                                    'query_params': [],
                                                                                                                    'request_body': True,
                                                                                                                    'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_notes': {'method': 'POST',
                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/notes/',
                                                                                                                 'path_params': ['award_public_id',
                                                                                                                                 'event_public_id',
                                                                                                                                 'workspace_public_id'],
                                                                                                                 'query_params': [],
                                                                                                                 'request_body': True,
                                                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_publish': {'method': 'POST',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/publish/',
                                                                                                      'path_params': ['award_public_id',
                                                                                                                      'event_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': False,
                                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_winners': {'method': 'POST',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/winners/',
                                                                                                      'path_params': ['award_public_id',
                                                                                                                      'event_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': True,
                                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes': {'method': 'POST',
                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/',
                                                                                   'path_params': ['event_public_id',
                                                                                                   'workspace_public_id'],
                                                                                   'query_params': [],
                                                                                   'request_body': True,
                                                                                   'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_check_ins': {'method': 'POST',
                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/check-ins/',
                                                                                 'path_params': ['event_public_id',
                                                                                                 'workspace_public_id'],
                                                                                 'query_params': [],
                                                                                 'request_body': True,
                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_checkins_scan': {'method': 'POST',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/checkins/scan/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': True,
                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_clone': {'method': 'POST',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/clone/',
                                                                             'path_params': ['event_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': True,
                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes': {'method': 'POST',
                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-project-attributes/',
                                                                                              'path_params': ['event_public_id',
                                                                                                              'workspace_public_id'],
                                                                                              'query_params': [],
                                                                                              'request_body': True,
                                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships': {'method': 'POST',
                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-relationships/',
                                                                                         'path_params': ['event_public_id',
                                                                                                         'workspace_public_id'],
                                                                                         'query_params': [],
                                                                                         'request_body': True,
                                                                                         'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_announcements_source_public_id_review': {'method': 'POST',
                                                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/announcements/{source_public_id}/review/',
                                                                                                                            'path_params': ['event_public_id',
                                                                                                                                            'source_public_id',
                                                                                                                                            'workspace_public_id'],
                                                                                                                            'query_params': [],
                                                                                                                            'request_body': True,
                                                                                                                            'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_audiences_preview': {'method': 'POST',
                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/audiences/preview/',
                                                                                                        'path_params': ['event_public_id',
                                                                                                                        'workspace_public_id'],
                                                                                                        'query_params': [],
                                                                                                        'request_body': True,
                                                                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_messages': {'method': 'POST',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/messages/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': True,
                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions': {'method': 'POST',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/questions/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': True,
                                                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions_source_public_id_review': {'method': 'POST',
                                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/questions/{source_public_id}/review/',
                                                                                                                        'path_params': ['event_public_id',
                                                                                                                                        'source_public_id',
                                                                                                                                        'workspace_public_id'],
                                                                                                                        'query_params': [],
                                                                                                                        'request_body': True,
                                                                                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders': {'method': 'POST',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/reminders/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': True,
                                                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders_reminder_public_id_cancel': {'method': 'POST',
                                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/reminders/{reminder_public_id}/cancel/',
                                                                                                                          'path_params': ['event_public_id',
                                                                                                                                          'reminder_public_id',
                                                                                                                                          'workspace_public_id'],
                                                                                                                          'query_params': [],
                                                                                                                          'request_body': False,
                                                                                                                          'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools': {'method': 'POST',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': True,
                                                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships': {'method': 'POST',
                                                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/memberships/',
                                                                                                                   'path_params': ['event_public_id',
                                                                                                                                   'pool_public_id',
                                                                                                                                   'workspace_public_id'],
                                                                                                                   'query_params': [],
                                                                                                                   'request_body': True,
                                                                                                                   'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_grants': {'method': 'POST',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-grants/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': True,
                                                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms': {'method': 'POST',
                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/',
                                                                             'path_params': ['event_public_id',
                                                                                             'workspace_public_id'],
                                                                             'query_params': [],
                                                                             'request_body': True,
                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_publish': {'method': 'POST',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/publish/',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'form_public_id',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': [],
                                                                                                    'request_body': False,
                                                                                                    'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_versions_version_public_id_restore': {'method': 'POST',
                                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/versions/{version_public_id}/restore/',
                                                                                                                               'path_params': ['event_public_id',
                                                                                                                                               'form_public_id',
                                                                                                                                               'version_public_id',
                                                                                                                                               'workspace_public_id'],
                                                                                                                               'query_params': [],
                                                                                                                               'request_body': False,
                                                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_conflicts': {'method': 'POST',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-conflicts/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': True,
                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations': {'method': 'POST',
                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-invitations/',
                                                                                         'path_params': ['event_public_id',
                                                                                                         'workspace_public_id'],
                                                                                         'query_params': [],
                                                                                         'request_body': True,
                                                                                         'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_locations': {'method': 'POST',
                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/',
                                                                                 'path_params': ['event_public_id',
                                                                                                 'workspace_public_id'],
                                                                                 'query_params': [],
                                                                                 'request_body': True,
                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_auto_assign': {'method': 'POST',
                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/auto-assign/',
                                                                                             'path_params': ['event_public_id',
                                                                                                             'workspace_public_id'],
                                                                                             'query_params': [],
                                                                                             'request_body': True,
                                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings': {'method': 'POST',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/',
                                                                                            'path_params': ['event_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': [],
                                                                                            'request_body': True,
                                                                                            'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_application': {'method': 'POST',
                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-application/',
                                                                                      'path_params': ['event_public_id',
                                                                                                      'workspace_public_id'],
                                                                                      'query_params': [],
                                                                                      'request_body': True,
                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team': {'method': 'POST',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/',
                                                                               'path_params': ['event_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': True,
                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites': {'method': 'POST',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/invites/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': True,
                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_leave': {'method': 'POST',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/leave/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'none'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_transfer_captain': {'method': 'POST',
                                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/transfer-captain/',
                                                                                                'path_params': ['event_public_id',
                                                                                                                'workspace_public_id'],
                                                                                                'query_params': [],
                                                                                                'request_body': True,
                                                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_bulk': {'method': 'POST',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/bulk/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': True,
                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation_reviews': {'method': 'POST',
                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/moderation/reviews/',
                                                                                                     'path_params': ['event_public_id',
                                                                                                                     'workspace_public_id'],
                                                                                                     'query_params': [],
                                                                                                     'request_body': True,
                                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks': {'method': 'POST',
                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/',
                                                                                   'path_params': ['event_public_id',
                                                                                                   'workspace_public_id'],
                                                                                   'query_params': [],
                                                                                   'request_body': True,
                                                                                   'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_reorder': {'method': 'POST',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/reorder/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': True,
                                                                                           'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_policies': {'method': 'POST',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': True,
                                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings': {'method': 'POST',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-bindings/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': True,
                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_debug': {'method': 'POST',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-debug/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': True,
                                                                                    'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_run': {'method': 'POST',
                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/retention/run/',
                                                                                             'path_params': ['event_public_id',
                                                                                                             'workspace_public_id'],
                                                                                             'query_params': [],
                                                                                             'request_body': True,
                                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_subjects_user_public_id_erase': {'method': 'POST',
                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/subjects/{user_public_id}/erase/',
                                                                                                             'path_params': ['event_public_id',
                                                                                                                             'user_public_id',
                                                                                                                             'workspace_public_id'],
                                                                                                             'query_params': [],
                                                                                                             'request_body': True,
                                                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_subjects_user_public_id_export': {'method': 'POST',
                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/subjects/{user_public_id}/export/',
                                                                                                              'path_params': ['event_public_id',
                                                                                                                              'user_public_id',
                                                                                                                              'workspace_public_id'],
                                                                                                              'query_params': [],
                                                                                                              'request_body': False,
                                                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects': {'method': 'POST',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': True,
                                                                                'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts': {'method': 'POST',
                                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/',
                                                                                                            'path_params': ['event_public_id',
                                                                                                                            'project_public_id',
                                                                                                                            'workspace_public_id'],
                                                                                                            'query_params': [],
                                                                                                            'request_body': True,
                                                                                                            'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_check_evidence': {'method': 'POST',
                                                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/check-evidence/',
                                                                                                                                              'path_params': ['artifact_public_id',
                                                                                                                                                              'event_public_id',
                                                                                                                                                              'project_public_id',
                                                                                                                                                              'workspace_public_id'],
                                                                                                                                              'query_params': [],
                                                                                                                                              'request_body': False,
                                                                                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_upload_intents_intent_public_id_complete': {'method': 'POST',
                                                                                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/upload-intents/{intent_public_id}/complete/',
                                                                                                                                                                        'path_params': ['artifact_public_id',
                                                                                                                                                                                        'event_public_id',
                                                                                                                                                                                        'intent_public_id',
                                                                                                                                                                                        'project_public_id',
                                                                                                                                                                                        'workspace_public_id'],
                                                                                                                                                                        'query_params': [],
                                                                                                                                                                        'request_body': True,
                                                                                                                                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_validate': {'method': 'POST',
                                                                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/validate/',
                                                                                                                                        'path_params': ['artifact_public_id',
                                                                                                                                                        'event_public_id',
                                                                                                                                                        'project_public_id',
                                                                                                                                                        'workspace_public_id'],
                                                                                                                                        'query_params': [],
                                                                                                                                        'request_body': False,
                                                                                                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_upload_intents': {'method': 'POST',
                                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/upload-intents/',
                                                                                                                           'path_params': ['event_public_id',
                                                                                                                                           'project_public_id',
                                                                                                                                           'workspace_public_id'],
                                                                                                                           'query_params': [],
                                                                                                                           'request_body': True,
                                                                                                                           'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments': {'method': 'POST',
                                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/comments/',
                                                                                                           'path_params': ['event_public_id',
                                                                                                                           'project_public_id',
                                                                                                                           'workspace_public_id'],
                                                                                                           'query_params': [],
                                                                                                           'request_body': True,
                                                                                                           'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments_comment_public_id_hide': {'method': 'POST',
                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/comments/{comment_public_id}/hide/',
                                                                                                                                  'path_params': ['comment_public_id',
                                                                                                                                                  'event_public_id',
                                                                                                                                                  'project_public_id',
                                                                                                                                                  'workspace_public_id'],
                                                                                                                                  'query_params': [],
                                                                                                                                  'request_body': False,
                                                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_checks': {'method': 'POST',
                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/checks/',
                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                     'project_public_id',
                                                                                                                                     'workspace_public_id'],
                                                                                                                     'query_params': [],
                                                                                                                     'request_body': False,
                                                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_decision': {'method': 'POST',
                                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/decision/',
                                                                                                                       'path_params': ['event_public_id',
                                                                                                                                       'project_public_id',
                                                                                                                                       'workspace_public_id'],
                                                                                                                       'query_params': [],
                                                                                                                       'request_body': True,
                                                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings': {'method': 'POST',
                                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/findings/',
                                                                                                                       'path_params': ['event_public_id',
                                                                                                                                       'project_public_id',
                                                                                                                                       'workspace_public_id'],
                                                                                                                       'query_params': [],
                                                                                                                       'request_body': True,
                                                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings_finding_public_id_close': {'method': 'POST',
                                                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/findings/{finding_public_id}/close/',
                                                                                                                                               'path_params': ['event_public_id',
                                                                                                                                                               'finding_public_id',
                                                                                                                                                               'project_public_id',
                                                                                                                                                               'workspace_public_id'],
                                                                                                                                               'query_params': [],
                                                                                                                                               'request_body': True,
                                                                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings_finding_public_id_respond': {'method': 'POST',
                                                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/findings/{finding_public_id}/respond/',
                                                                                                                                                 'path_params': ['event_public_id',
                                                                                                                                                                 'finding_public_id',
                                                                                                                                                                 'project_public_id',
                                                                                                                                                                 'workspace_public_id'],
                                                                                                                                                 'query_params': [],
                                                                                                                                                 'request_body': True,
                                                                                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_members': {'method': 'POST',
                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/members/',
                                                                                                          'path_params': ['event_public_id',
                                                                                                                          'project_public_id',
                                                                                                                          'workspace_public_id'],
                                                                                                          'query_params': [],
                                                                                                          'request_body': True,
                                                                                                          'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_notes': {'method': 'POST',
                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/mentor-notes/',
                                                                                                               'path_params': ['event_public_id',
                                                                                                                               'project_public_id',
                                                                                                                               'workspace_public_id'],
                                                                                                               'query_params': [],
                                                                                                               'request_body': True,
                                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_finalize': {'method': 'POST',
                                                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/finalize/',
                                                                                                                                       'path_params': ['event_public_id',
                                                                                                                                                       'project_public_id',
                                                                                                                                                       'stage_public_id',
                                                                                                                                                       'workspace_public_id'],
                                                                                                                                       'query_params': [],
                                                                                                                                       'request_body': True,
                                                                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_reopen': {'method': 'POST',
                                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/reopen/',
                                                                                                                                     'path_params': ['event_public_id',
                                                                                                                                                     'project_public_id',
                                                                                                                                                     'stage_public_id',
                                                                                                                                                     'workspace_public_id'],
                                                                                                                                     'query_params': [],
                                                                                                                                     'request_body': True,
                                                                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_event': {'method': 'POST',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/records/event/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': False,
                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_judge': {'method': 'POST',
                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/records/judge/',
                                                                                     'path_params': ['event_public_id',
                                                                                                     'workspace_public_id'],
                                                                                     'query_params': [],
                                                                                     'request_body': True,
                                                                                     'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_project': {'method': 'POST',
                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/records/project/',
                                                                                       'path_params': ['event_public_id',
                                                                                                       'workspace_public_id'],
                                                                                       'query_params': [],
                                                                                       'request_body': True,
                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes': {'method': 'POST',
                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-invite-codes/',
                                                                                                 'path_params': ['event_public_id',
                                                                                                                 'workspace_public_id'],
                                                                                                 'query_params': [],
                                                                                                 'request_body': True,
                                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches': {'method': 'POST',
                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/',
                                                                                      'path_params': ['event_public_id',
                                                                                                      'workspace_public_id'],
                                                                                      'query_params': [],
                                                                                      'request_body': True,
                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions': {'method': 'POST',
                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-transitions/',
                                                                                         'path_params': ['event_public_id',
                                                                                                         'workspace_public_id'],
                                                                                         'query_params': [],
                                                                                         'request_body': True,
                                                                                         'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages': {'method': 'POST',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': [],
                                                                              'request_body': True,
                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_advance': {'method': 'POST',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/advance/',
                                                                                                      'path_params': ['event_public_id',
                                                                                                                      'stage_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': True,
                                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans': {'method': 'POST',
                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/',
                                                                                                               'path_params': ['event_public_id',
                                                                                                                               'stage_public_id',
                                                                                                                               'workspace_public_id'],
                                                                                                               'query_params': [],
                                                                                                               'request_body': True,
                                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals': {'method': 'POST',
                                                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/appeals/',
                                                                                                                                      'path_params': ['event_public_id',
                                                                                                                                                      'plan_public_id',
                                                                                                                                                      'stage_public_id',
                                                                                                                                                      'workspace_public_id'],
                                                                                                                                      'query_params': [],
                                                                                                                                      'request_body': True,
                                                                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals_appeal_public_id_decide': {'method': 'POST',
                                                                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/appeals/{appeal_public_id}/decide/',
                                                                                                                                                              'path_params': ['appeal_public_id',
                                                                                                                                                                              'event_public_id',
                                                                                                                                                                              'plan_public_id',
                                                                                                                                                                              'stage_public_id',
                                                                                                                                                                              'workspace_public_id'],
                                                                                                                                                              'query_params': [],
                                                                                                                                                              'request_body': True,
                                                                                                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_activate': {'method': 'POST',
                                                                                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/activate/',
                                                                                                                                                   'path_params': ['event_public_id',
                                                                                                                                                                   'plan_public_id',
                                                                                                                                                                   'stage_public_id',
                                                                                                                                                                   'workspace_public_id'],
                                                                                                                                                   'query_params': [],
                                                                                                                                                   'request_body': True,
                                                                                                                                                   'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_activate_optimized': {'method': 'POST',
                                                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/activate-optimized/',
                                                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                                                             'plan_public_id',
                                                                                                                                                                             'stage_public_id',
                                                                                                                                                                             'workspace_public_id'],
                                                                                                                                                             'query_params': [],
                                                                                                                                                             'request_body': True,
                                                                                                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_compare': {'method': 'POST',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/compare/',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': True,
                                                                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_dropout_simulation': {'method': 'POST',
                                                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/dropout-simulation/',
                                                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                                                             'plan_public_id',
                                                                                                                                                                             'stage_public_id',
                                                                                                                                                                             'workspace_public_id'],
                                                                                                                                                             'query_params': [],
                                                                                                                                                             'request_body': True,
                                                                                                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_preview': {'method': 'POST',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/preview/',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': True,
                                                                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_rebalance': {'method': 'POST',
                                                                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/rebalance/',
                                                                                                                                                    'path_params': ['event_public_id',
                                                                                                                                                                    'plan_public_id',
                                                                                                                                                                    'stage_public_id',
                                                                                                                                                                    'workspace_public_id'],
                                                                                                                                                    'query_params': [],
                                                                                                                                                    'request_body': True,
                                                                                                                                                    'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots': {'method': 'POST',
                                                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/',
                                                                                                                                      'path_params': ['event_public_id',
                                                                                                                                                      'plan_public_id',
                                                                                                                                                      'stage_public_id',
                                                                                                                                                      'workspace_public_id'],
                                                                                                                                      'query_params': [],
                                                                                                                                      'request_body': True,
                                                                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_ballots': {'method': 'POST',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/ballots/',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': True,
                                                                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_normalization_runs': {'method': 'POST',
                                                                                                                                                 'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/normalization-runs/',
                                                                                                                                                 'path_params': ['event_public_id',
                                                                                                                                                                 'plan_public_id',
                                                                                                                                                                 'stage_public_id',
                                                                                                                                                                 'workspace_public_id'],
                                                                                                                                                 'query_params': [],
                                                                                                                                                 'request_body': True,
                                                                                                                                                 'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_comparisons': {'method': 'POST',
                                                                                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/comparisons/',
                                                                                                                                                   'path_params': ['event_public_id',
                                                                                                                                                                   'plan_public_id',
                                                                                                                                                                   'stage_public_id',
                                                                                                                                                                   'workspace_public_id'],
                                                                                                                                                   'query_params': [],
                                                                                                                                                   'request_body': True,
                                                                                                                                                   'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_publish_results': {'method': 'POST',
                                                                                                                                                       'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/publish-results/',
                                                                                                                                                       'path_params': ['event_public_id',
                                                                                                                                                                       'plan_public_id',
                                                                                                                                                                       'stage_public_id',
                                                                                                                                                                       'workspace_public_id'],
                                                                                                                                                       'query_params': [],
                                                                                                                                                       'request_body': True,
                                                                                                                                                       'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_runs': {'method': 'POST',
                                                                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/runs/',
                                                                                                                                            'path_params': ['event_public_id',
                                                                                                                                                            'plan_public_id',
                                                                                                                                                            'stage_public_id',
                                                                                                                                                            'workspace_public_id'],
                                                                                                                                            'query_params': [],
                                                                                                                                            'request_body': True,
                                                                                                                                            'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_results': {'method': 'POST',
                                                                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/publish-results/',
                                                                                                                                              'path_params': ['event_public_id',
                                                                                                                                                              'plan_public_id',
                                                                                                                                                              'stage_public_id',
                                                                                                                                                              'workspace_public_id'],
                                                                                                                                              'query_params': [],
                                                                                                                                              'request_body': True,
                                                                                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_rubric': {'method': 'POST',
                                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/publish-rubric/',
                                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                                             'plan_public_id',
                                                                                                                                                             'stage_public_id',
                                                                                                                                                             'workspace_public_id'],
                                                                                                                                             'query_params': [],
                                                                                                                                             'request_body': False,
                                                                                                                                             'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_rubric_lab': {'method': 'POST',
                                                                                                                                         'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/rubric-lab/',
                                                                                                                                         'path_params': ['event_public_id',
                                                                                                                                                         'plan_public_id',
                                                                                                                                                         'stage_public_id',
                                                                                                                                                         'workspace_public_id'],
                                                                                                                                         'query_params': [],
                                                                                                                                         'request_body': True,
                                                                                                                                         'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_rubric_versions_rubric_version_public_id_restore': {'method': 'POST',
                                                                                                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/rubric-versions/{rubric_version_public_id}/restore/',
                                                                                                                                                                               'path_params': ['event_public_id',
                                                                                                                                                                                               'plan_public_id',
                                                                                                                                                                                               'rubric_version_public_id',
                                                                                                                                                                                               'stage_public_id',
                                                                                                                                                                                               'workspace_public_id'],
                                                                                                                                                                               'query_params': [],
                                                                                                                                                                               'request_body': False,
                                                                                                                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_sensitivity': {'method': 'POST',
                                                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/sensitivity/',
                                                                                                                                          'path_params': ['event_public_id',
                                                                                                                                                          'plan_public_id',
                                                                                                                                                          'stage_public_id',
                                                                                                                                                          'workspace_public_id'],
                                                                                                                                          'query_params': [],
                                                                                                                                          'request_body': True,
                                                                                                                                          'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_external_qualifiers': {'method': 'POST',
                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/external-qualifiers/',
                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                  'stage_public_id',
                                                                                                                                  'workspace_public_id'],
                                                                                                                  'query_params': [],
                                                                                                                  'request_body': True,
                                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_status': {'method': 'POST',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/status/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': [],
                                                                              'request_body': True,
                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_team_invites_redeem': {'method': 'POST',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/team-invites/redeem/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': True,
                                                                                           'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates': {'method': 'POST',
                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/',
                                                                                      'path_params': ['event_public_id',
                                                                                                      'workspace_public_id'],
                                                                                      'query_params': [],
                                                                                      'request_body': True,
                                                                                      'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks': {'method': 'POST',
                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/',
                                                                              'path_params': ['event_public_id',
                                                                                              'workspace_public_id'],
                                                                              'query_params': [],
                                                                              'request_body': True,
                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_abuse_signals_signal_public_id_resolve': {'method': 'POST',
                                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/abuse-signals/{signal_public_id}/resolve/',
                                                                                                                          'path_params': ['event_public_id',
                                                                                                                                          'signal_public_id',
                                                                                                                                          'workspace_public_id'],
                                                                                                                          'query_params': [],
                                                                                                                          'request_body': True,
                                                                                                                          'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_publish_results': {'method': 'POST',
                                                                                                   'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/publish-results/',
                                                                                                   'path_params': ['event_public_id',
                                                                                                                   'workspace_public_id'],
                                                                                                   'query_params': [],
                                                                                                   'request_body': False,
                                                                                                   'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_tokens': {'method': 'POST',
                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/tokens/',
                                                                                          'path_params': ['event_public_id',
                                                                                                          'workspace_public_id'],
                                                                                          'query_params': [],
                                                                                          'request_body': True,
                                                                                          'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_request_email_token': {'method': 'POST',
                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/request-email-token/',
                                                                                                  'path_params': ['event_public_id',
                                                                                                                  'workspace_public_id'],
                                                                                                  'query_params': [],
                                                                                                  'request_body': True,
                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_votes': {'method': 'POST',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/votes/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': True,
                                                                                    'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_events_event_public_id_workflow_presets_apply': {'method': 'POST',
                                                                                              'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/workflow-presets/apply/',
                                                                                              'path_params': ['event_public_id',
                                                                                                              'workspace_public_id'],
                                                                                              'query_params': [],
                                                                                              'request_body': True,
                                                                                              'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_inbox_recipient_public_id_read': {'method': 'POST',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/inbox/{recipient_public_id}/read/',
                                                                               'path_params': ['recipient_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': False,
                                                                               'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_members': {'method': 'POST',
                                                        'path': '/api/v1/workspaces/{workspace_public_id}/members/',
                                                        'path_params': ['workspace_public_id'],
                                                        'query_params': [],
                                                        'request_body': True,
                                                        'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_my_judge_invitations_invitation_public_id_respond': {'method': 'POST',
                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/my-judge-invitations/{invitation_public_id}/respond/',
                                                                                                  'path_params': ['invitation_public_id',
                                                                                                                  'workspace_public_id'],
                                                                                                  'query_params': [],
                                                                                                  'request_body': True,
                                                                                                  'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_taxonomies': {'method': 'POST',
                                                           'path': '/api/v1/workspaces/{workspace_public_id}/taxonomies/',
                                                           'path_params': ['workspace_public_id'],
                                                           'query_params': [],
                                                           'request_body': True,
                                                           'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_webhooks': {'method': 'POST',
                                                         'path': '/api/v1/workspaces/{workspace_public_id}/webhooks/',
                                                         'path_params': ['workspace_public_id'],
                                                         'query_params': [],
                                                         'request_body': True,
                                                         'response_kind': 'json'},
 'post_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries_delivery_public_id_replay': {'method': 'POST',
                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/deliveries/{delivery_public_id}/replay/',
                                                                                                                     'path_params': ['delivery_public_id',
                                                                                                                                     'subscription_public_id',
                                                                                                                                     'workspace_public_id'],
                                                                                                                     'query_params': [],
                                                                                                                     'request_body': False,
                                                                                                                     'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_projects_project_public_id_stance': {'method': 'PUT',
                                                                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/projects/{project_public_id}/stance/',
                                                                                                                                            'path_params': ['award_public_id',
                                                                                                                                                            'event_public_id',
                                                                                                                                                            'project_public_id',
                                                                                                                                                            'workspace_public_id'],
                                                                                                                                            'query_params': [],
                                                                                                                                            'request_body': True,
                                                                                                                                            'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_sponsors_user_public_id': {'method': 'PUT',
                                                                                                                     'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/sponsors/{user_public_id}/',
                                                                                                                     'path_params': ['award_public_id',
                                                                                                                                     'event_public_id',
                                                                                                                                     'user_public_id',
                                                                                                                                     'workspace_public_id'],
                                                                                                                     'query_params': [],
                                                                                                                     'request_body': False,
                                                                                                                     'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_rules': {'method': 'PUT',
                                                                                'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-rules/',
                                                                                'path_params': ['event_public_id',
                                                                                                'workspace_public_id'],
                                                                                'query_params': [],
                                                                                'request_body': True,
                                                                                'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_rules': {'method': 'PUT',
                                                                                        'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/eligibility-rules/',
                                                                                        'path_params': ['event_public_id',
                                                                                                        'workspace_public_id'],
                                                                                        'query_params': [],
                                                                                        'request_body': True,
                                                                                        'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id': {'method': 'PUT',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'form_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': True,
                                                                                           'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profile': {'method': 'PUT',
                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/profile/',
                                                                                          'path_params': ['event_public_id',
                                                                                                          'workspace_public_id'],
                                                                                          'query_params': [],
                                                                                          'request_body': True,
                                                                                          'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_my_attendance': {'method': 'PUT',
                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-attendance/',
                                                                                    'path_params': ['event_public_id',
                                                                                                    'workspace_public_id'],
                                                                                    'query_params': [],
                                                                                    'request_body': True,
                                                                                    'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_policy': {'method': 'PUT',
                                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/retention-policy/',
                                                                                               'path_params': ['event_public_id',
                                                                                                               'workspace_public_id'],
                                                                                               'query_params': [],
                                                                                               'request_body': True,
                                                                                               'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms_version_public_id_response': {'method': 'PUT',
                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/forms/{version_public_id}/response/',
                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                  'project_public_id',
                                                                                                                                                  'version_public_id',
                                                                                                                                                  'workspace_public_id'],
                                                                                                                                  'query_params': [],
                                                                                                                                  'request_body': True,
                                                                                                                                  'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_location': {'method': 'PUT',
                                                                                                          'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/location/',
                                                                                                          'path_params': ['event_public_id',
                                                                                                                          'project_public_id',
                                                                                                                          'workspace_public_id'],
                                                                                                          'query_params': [],
                                                                                                          'request_body': True,
                                                                                                          'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id': {'method': 'PUT',
                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/',
                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                             'project_public_id',
                                                                                                                                             'stage_public_id',
                                                                                                                                             'workspace_public_id'],
                                                                                                                             'query_params': [],
                                                                                                                             'request_body': True,
                                                                                                                             'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_tags': {'method': 'PUT',
                                                                                                      'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/tags/',
                                                                                                      'path_params': ['event_public_id',
                                                                                                                      'project_public_id',
                                                                                                                      'workspace_public_id'],
                                                                                                      'query_params': [],
                                                                                                      'request_body': True,
                                                                                                      'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules_surface': {'method': 'PUT',
                                                                                                    'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/publication-schedules/{surface}/',
                                                                                                    'path_params': ['event_public_id',
                                                                                                                    'surface',
                                                                                                                    'workspace_public_id'],
                                                                                                    'query_params': ['surface'],
                                                                                                    'request_body': True,
                                                                                                    'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_settings': {'method': 'PUT',
                                                                                            'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-settings/',
                                                                                            'path_params': ['event_public_id',
                                                                                                            'workspace_public_id'],
                                                                                            'query_params': [],
                                                                                            'request_body': True,
                                                                                            'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft': {'method': 'PUT',
                                                                                                                                                             'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/{project_public_id}/draft/',
                                                                                                                                                             'path_params': ['event_public_id',
                                                                                                                                                                             'plan_public_id',
                                                                                                                                                                             'project_public_id',
                                                                                                                                                                             'stage_public_id',
                                                                                                                                                                             'workspace_public_id'],
                                                                                                                                                             'query_params': [],
                                                                                                                                                             'request_body': True,
                                                                                                                                                             'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_projects': {'method': 'PUT',
                                                                                                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration-projects/',
                                                                                                                                                  'path_params': ['event_public_id',
                                                                                                                                                                  'plan_public_id',
                                                                                                                                                                  'stage_public_id',
                                                                                                                                                                  'workspace_public_id'],
                                                                                                                                                  'query_params': [],
                                                                                                                                                  'request_body': True,
                                                                                                                                                  'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_events_event_public_id_taxonomy_assignments': {'method': 'PUT',
                                                                                           'path': '/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/taxonomy-assignments/',
                                                                                           'path_params': ['event_public_id',
                                                                                                           'workspace_public_id'],
                                                                                           'query_params': [],
                                                                                           'request_body': True,
                                                                                           'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_judge_expertise_judge_public_id': {'method': 'PUT',
                                                                               'path': '/api/v1/workspaces/{workspace_public_id}/judge-expertise/{judge_public_id}/',
                                                                               'path_params': ['judge_public_id',
                                                                                               'workspace_public_id'],
                                                                               'query_params': [],
                                                                               'request_body': True,
                                                                               'response_kind': 'json'},
 'put_api_v1_workspaces_workspace_public_id_my_judge_expertise': {'method': 'PUT',
                                                                  'path': '/api/v1/workspaces/{workspace_public_id}/my-judge-expertise/',
                                                                  'path_params': ['workspace_public_id'],
                                                                  'query_params': [],
                                                                  'request_body': True,
                                                                  'response_kind': 'json'}}
