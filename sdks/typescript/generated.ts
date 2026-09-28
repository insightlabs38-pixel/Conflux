// Generated from docs/api/openapi.yaml. Run scripts/generate_sdks.py.

export type AbuseSignalSchema = {
  public_id: string;
  signal_type: string;
  detail: string;
  evidence: unknown;
  occurred_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string;
};

export type InputOfAbuseSignalSchema = {
  public_id: string;
  signal_type: string;
  detail: string;
  evidence: unknown;
  occurred_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string;
};

export type AccessEnum = "roles" | "any_authenticated" | "public" | "unknown";

export type InputOfAccessEnum =
  "roles" | "any_authenticated" | "public" | "unknown";

export type AccessibilityWarning = {
  category: CategoryEnum;
  severity: string;
  message: string;
  block_public_id: string | null;
};

export type InputOfAccessibilityWarning = {
  category: InputOfCategoryEnum;
  severity: string;
  message: string;
  block_public_id: string | null;
};

export type ActionEnum = "submit" | "join" | "advance" | "vote" | "award";

export type InputOfActionEnum =
  "submit" | "join" | "advance" | "vote" | "award";

export type AddProjectMemberInput = { user: string };

export type InputOfAddProjectMemberInput = { user: string };

export type AdvancedSubjectSchema = {
  subject_type: string;
  subject_id: string;
};

export type InputOfAdvancedSubjectSchema = {
  subject_type: string;
  subject_id: string;
};

export type AdvancementCandidateSchema = {
  subject_type: string;
  subject_id: string;
  score?: number | null;
  track_id?: string | null;
};

export type InputOfAdvancementCandidateSchema = {
  subject_type: string;
  subject_id: string;
  score?: number | null;
  track_id?: string | null;
};

export type AdvancementEvidenceSchema = {
  created_at: string;
  actor: string | null;
  stage_public_id: string;
  metadata: unknown;
};

export type InputOfAdvancementEvidenceSchema = {
  created_at: string;
  actor: string | null;
  stage_public_id: string;
  metadata: unknown;
};

export type AdvancementInputSchema = {
  to_stage: string;
  strategy: string;
  params?: unknown;
  candidates: AdvancementCandidateSchema[];
};

export type InputOfAdvancementInputSchema = {
  to_stage: string;
  strategy: string;
  params?: unknown;
  candidates: InputOfAdvancementCandidateSchema[];
};

export type AdvancementResultSchema = { advanced: AdvancedSubjectSchema[] };

export type InputOfAdvancementResultSchema = {
  advanced: InputOfAdvancedSubjectSchema[];
};

export type AdvancementStrategiesSchema = { strategies: string[] };

export type InputOfAdvancementStrategiesSchema = { strategies: string[] };

export type AgreementCriterionSchema = {
  project: string;
  project_name: string;
  criterion_id: string;
  scores: Record<string, number>;
  mean: number;
  range: number;
  stdev: number;
};

export type InputOfAgreementCriterionSchema = {
  project: string;
  project_name: string;
  criterion_id: string;
  scores: Record<string, number>;
  mean: number;
  range: number;
  stdev: number;
};

export type AgreementRankingSchema = {
  judge_a: string;
  judge_b: string;
  shared_candidates: number;
  tau: number | null;
};

export type InputOfAgreementRankingSchema = {
  judge_a: string;
  judge_b: string;
  shared_candidates: number;
  tau: number | null;
};

export type AgreementSummarySchema = {
  criteria: AgreementCriterionSchema[];
  rankings: AgreementRankingSchema[];
};

export type InputOfAgreementSummarySchema = {
  criteria: InputOfAgreementCriterionSchema[];
  rankings: InputOfAgreementRankingSchema[];
};

export type Announcement = {
  public_id: string;
  title: string;
  body?: string;
  posted_by: string;
  created_at: string;
  hidden_at: string | null;
  version: number;
};

export type InputOfAnnouncement = { title: string; body?: string };

export type AnnouncementReviewInput = {
  version: number;
  status: AnnouncementReviewInputStatusEnum;
  note: string;
};

export type InputOfAnnouncementReviewInput = {
  version: number;
  status: InputOfAnnouncementReviewInputStatusEnum;
  note: string;
};

export type AnnouncementReviewInputStatusEnum = "published" | "hidden";

export type InputOfAnnouncementReviewInputStatusEnum = "published" | "hidden";

export type AnnouncementReviewOutput = {
  public_id: string;
  title: string;
  body: string;
  created_at: string;
  version: number;
  hidden_at: string | null;
};

export type InputOfAnnouncementReviewOutput = {};

export type AppealDecisionInputSchema = {
  status: AppealDecisionInputSchemaStatusEnum;
  decision_note?: string;
};

export type InputOfAppealDecisionInputSchema = {
  status: InputOfAppealDecisionInputSchemaStatusEnum;
  decision_note?: string;
};

export type AppealDecisionInputSchemaStatusEnum =
  "upheld" | "overturned" | "dismissed";

export type InputOfAppealDecisionInputSchemaStatusEnum =
  "upheld" | "overturned" | "dismissed";

export type AppealInputSchema = { project: string; body: string };

export type InputOfAppealInputSchema = { project: string; body: string };

export type AppealSchema = {
  public_id: string;
  project: string;
  project_name: string;
  submitted_by: string;
  submitted_by_username: string;
  body: string;
  status: string;
  decision_note: string;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
};

export type InputOfAppealSchema = {
  public_id: string;
  project: string;
  project_name: string;
  submitted_by: string;
  submitted_by_username: string;
  body: string;
  status: string;
  decision_note: string;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
};

export type ApplicationDecisionInputSchema = {
  decision: ApplicationDecisionInputSchemaDecisionEnum;
};

export type InputOfApplicationDecisionInputSchema = {
  decision: InputOfApplicationDecisionInputSchemaDecisionEnum;
};

export type ApplicationDecisionInputSchemaDecisionEnum =
  "approved" | "waitlisted" | "rejected";

export type InputOfApplicationDecisionInputSchemaDecisionEnum =
  "approved" | "waitlisted" | "rejected";

export type ApplyInput = { apply?: boolean; kind?: ApplyInputKindEnum };

export type InputOfApplyInput = {
  apply?: boolean;
  kind?: InputOfApplyInputKindEnum;
};

export type ApplyInputKindEnum = "table" | "booth";

export type InputOfApplyInputKindEnum = "table" | "booth";

export type ApplyToEventInputSchema = { note?: string; code?: string };

export type InputOfApplyToEventInputSchema = { note?: string; code?: string };

export type ArchiveImportInput = {
  name: string;
  slug: string;
  archive: unknown;
};

export type InputOfArchiveImportInput = {
  name: string;
  slug: string;
  archive: unknown;
};

export type ArchiveOutput = {
  format_version: number;
  mode: string;
  event: Record<string, unknown>;
  tracks?: Record<string, unknown>[];
  base_prizes?: Record<string, unknown>[];
  stages?: Record<string, unknown>[];
  stage_transitions?: Record<string, unknown>[];
  forms?: Record<string, unknown>[];
  policies?: Record<string, unknown>[];
  temporal_gates?: Record<string, unknown>[];
  policy_bindings?: Record<string, unknown>[];
  awards?: Record<string, unknown>[];
  projects?: Record<string, unknown>[];
  evaluation_plans?: Record<string, unknown>[];
  pages?: Record<string, unknown>[];
  tables?: Record<string, unknown>;
  users?: Record<string, unknown>[];
  provenance?: Record<string, unknown>[];
};

export type InputOfArchiveOutput = {
  format_version: number;
  mode: string;
  event: Record<string, unknown>;
  tracks?: Record<string, unknown>[];
  base_prizes?: Record<string, unknown>[];
  stages?: Record<string, unknown>[];
  stage_transitions?: Record<string, unknown>[];
  forms?: Record<string, unknown>[];
  policies?: Record<string, unknown>[];
  temporal_gates?: Record<string, unknown>[];
  policy_bindings?: Record<string, unknown>[];
  awards?: Record<string, unknown>[];
  projects?: Record<string, unknown>[];
  evaluation_plans?: Record<string, unknown>[];
  pages?: Record<string, unknown>[];
  tables?: Record<string, unknown>;
  users?: Record<string, unknown>[];
  provenance?: Record<string, unknown>[];
};

export type ArchivePreviewChange = {
  field: string;
  source: unknown;
  imported: unknown;
};

export type InputOfArchivePreviewChange = {
  field: string;
  source: unknown;
  imported: unknown;
};

export type ArchivePreviewOutput = {
  format_version: number;
  mode: string;
  migration_steps: string[];
  deprecations: string[];
  event_changes: ArchivePreviewChange[];
  sections: ArchivePreviewSection[];
  ignored_sections: string[];
};

export type InputOfArchivePreviewOutput = {
  format_version: number;
  mode: string;
  migration_steps: string[];
  deprecations: string[];
  event_changes: InputOfArchivePreviewChange[];
  sections: InputOfArchivePreviewSection[];
  ignored_sections: string[];
};

export type ArchivePreviewSection = {
  section: string;
  source_count: number;
  imported_count: number;
};

export type InputOfArchivePreviewSection = {
  section: string;
  source_count: number;
  imported_count: number;
};

export type ArtifactKindEnum =
  | "file"
  | "image"
  | "video"
  | "external_video"
  | "repository"
  | "live_url"
  | "document"
  | "dataset"
  | "secret";

export type InputOfArtifactKindEnum =
  | "file"
  | "image"
  | "video"
  | "external_video"
  | "repository"
  | "live_url"
  | "document"
  | "dataset"
  | "secret";

export type ArtifactSchema = {
  public_id: string;
  kind: string;
  visibility: string;
  title: string;
  external_url: string;
  content_type: string;
  byte_size: number | null;
  status: string;
  validation: ValidationSchema | null;
  ci_evidence?: ValidationSchema[];
  download_url?: string;
};

export type InputOfArtifactSchema = {
  public_id: string;
  kind: string;
  visibility: string;
  title: string;
  external_url: string;
  content_type: string;
  byte_size: number | null;
  status: string;
  validation: InputOfValidationSchema | null;
  ci_evidence?: InputOfValidationSchema[];
  download_url?: string;
};

export type Assignment = { judge: string; project: string };

export type InputOfAssignment = {};

export type AssignmentActivateInputSchema = { coverage?: number };

export type InputOfAssignmentActivateInputSchema = { coverage?: number };

export type AssignmentCompareInputSchema = { coverage?: number };

export type InputOfAssignmentCompareInputSchema = { coverage?: number };

export type AssignmentCompareSchema = {
  heuristic: AssignmentCoveragePreviewSchema;
  optimized: AssignmentCoveragePreviewSchema;
};

export type InputOfAssignmentCompareSchema = {
  heuristic: InputOfAssignmentCoveragePreviewSchema;
  optimized: InputOfAssignmentCoveragePreviewSchema;
};

export type AssignmentCoveragePreviewSchema = {
  solver: string;
  coverage: number;
  candidate_count: number;
  judge_count: number;
  assignment_count: number;
  load_by_judge: Record<string, number>;
  conflict_count: number;
  connectivity: Record<string, unknown>;
};

export type InputOfAssignmentCoveragePreviewSchema = {
  solver: string;
  coverage: number;
  candidate_count: number;
  judge_count: number;
  assignment_count: number;
  load_by_judge: Record<string, number>;
  conflict_count: number;
  connectivity: Record<string, unknown>;
};

export type AssignmentInput = {
  taxonomy: string;
  subject: SubjectInput;
  terms: string[];
};

export type InputOfAssignmentInput = {
  taxonomy: string;
  subject: InputOfSubjectInput;
  terms: string[];
};

export type AssignmentOutput = {
  taxonomy: string;
  term: string;
  subject: Record<string, unknown>;
};

export type InputOfAssignmentOutput = {
  taxonomy: string;
  term: string;
  subject: Record<string, unknown>;
};

export type AssignmentPreviewInputSchema = { coverage_options?: number[] };

export type InputOfAssignmentPreviewInputSchema = {
  coverage_options?: number[];
};

export type AssignmentRebalanceInputSchema = {
  drop_judges?: string[];
  coverage?: number;
};

export type InputOfAssignmentRebalanceInputSchema = {
  drop_judges?: string[];
  coverage?: number;
};

export type AssignmentResponseInput = {
  status: AssignmentResponseInputStatusEnum;
  reason?: string;
};

export type InputOfAssignmentResponseInput = {
  status: InputOfAssignmentResponseInputStatusEnum;
  reason?: string;
};

export type AssignmentResponseInputStatusEnum = "accepted" | "declined";

export type InputOfAssignmentResponseInputStatusEnum = "accepted" | "declined";

export type AssignmentVersion = {
  public_id: string;
  number: number;
  coverage: number;
  evidence?: unknown;
  assignments: Assignment[];
  created_at: string;
};

export type InputOfAssignmentVersion = {
  number: number;
  coverage: number;
  evidence?: unknown;
};

export type AttemptOutput = {
  public_id: string;
  destination: string;
  body: string;
  headers: Record<string, string>;
  started_at: string;
  completed_at: string | null;
  status_code: number | null;
  error: string;
};

export type InputOfAttemptOutput = {
  public_id: string;
  destination: string;
  body: string;
  headers: Record<string, string>;
  started_at: string;
  completed_at: string | null;
  status_code: number | null;
  error: string;
};

export type AttendanceInput = { mode: AttendanceInputModeEnum };

export type InputOfAttendanceInput = { mode: InputOfAttendanceInputModeEnum };

export type AttendanceInputModeEnum = "in_person" | "remote" | "not_attending";

export type InputOfAttendanceInputModeEnum =
  "in_person" | "remote" | "not_attending";

export type AudienceKindSchema = {
  key: string;
  label: string;
  param_names: string[];
  options: unknown;
};

export type InputOfAudienceKindSchema = {
  key: string;
  label: string;
  param_names: string[];
  options: unknown;
};

export type AudienceMemberSchema = { public_id: string; username: string };

export type InputOfAudienceMemberSchema = {
  public_id: string;
  username: string;
};

export type AudiencePreviewInputSchema = {
  audience_kind: string;
  audience_params?: unknown;
};

export type InputOfAudiencePreviewInputSchema = {
  audience_kind: string;
  audience_params?: unknown;
};

export type AudiencePreviewSchema = {
  count: number;
  sample: AudienceMemberSchema[];
};

export type InputOfAudiencePreviewSchema = {
  count: number;
  sample: InputOfAudienceMemberSchema[];
};

export type AuditEventSchema = {
  public_id: string;
  actor: string | null;
  action: string;
  target_type: string;
  target_id: string;
  metadata: unknown;
  created_at: string;
};

export type InputOfAuditEventSchema = {
  public_id: string;
  actor: string | null;
  action: string;
  target_type: string;
  target_id: string;
  metadata: unknown;
  created_at: string;
};

export type AuthzDryRunInputSchema = {
  path: string;
  method: MethodEnum;
  subject_kind: SubjectKindEnum;
  subject: string;
};

export type InputOfAuthzDryRunInputSchema = {
  path: string;
  method: InputOfMethodEnum;
  subject_kind: InputOfSubjectKindEnum;
  subject: string;
};

export type AuthzDryRunOutputSchema = {
  allowed: boolean;
  mode: AuthzDryRunOutputSchemaModeEnum;
  access?: string;
  roles?: string[];
  actual_roles?: string[];
};

export type InputOfAuthzDryRunOutputSchema = {
  allowed: boolean;
  mode: InputOfAuthzDryRunOutputSchemaModeEnum;
  access?: string;
  roles?: string[];
  actual_roles?: string[];
};

export type AuthzDryRunOutputSchemaModeEnum = "live" | "hypothetical";

export type InputOfAuthzDryRunOutputSchemaModeEnum = "live" | "hypothetical";

export type AwardInput = {
  name: string;
  description?: string;
  eligibility_track?: string | null;
  require_finalized_submission?: boolean;
  selection_source: SelectionSourceEnum;
  evaluation_plan?: string | null;
  winner_count: number;
  allow_stacking?: boolean;
  conflict_group?: string;
};

export type InputOfAwardInput = {
  name: string;
  description?: string;
  eligibility_track?: string | null;
  require_finalized_submission?: boolean;
  selection_source: InputOfSelectionSourceEnum;
  evaluation_plan?: string | null;
  winner_count: number;
  allow_stacking?: boolean;
  conflict_group?: string;
};

export type AwardOutput = {
  public_id: string;
  name: string;
  description: string;
  eligibility_track: string | null;
  require_finalized_submission: boolean;
  selection_source: string;
  evaluation_plan: string | null;
  winner_count: number;
  allow_stacking: boolean;
  conflict_group: string;
  published_at: string | null;
  components: ComponentOutput[];
  winners: WinnerOutput[];
  sponsor_contacts: string[];
};

export type InputOfAwardOutput = {
  public_id: string;
  name: string;
  description: string;
  eligibility_track: string | null;
  require_finalized_submission: boolean;
  selection_source: string;
  evaluation_plan: string | null;
  winner_count: number;
  allow_stacking: boolean;
  conflict_group: string;
  published_at: string | null;
  components: InputOfComponentOutput[];
  winners: InputOfWinnerOutput[];
  sponsor_contacts: string[];
};

export type AwardProposalItem = {
  award: string;
  name: string;
  existing: string[];
  proposed: string[];
  unfilled: number;
  blocker: string | null;
};

export type InputOfAwardProposalItem = {
  award: string;
  name: string;
  existing: string[];
  proposed: string[];
  unfilled: number;
  blocker: string | null;
};

export type AwardProposalOutput = {
  search_limited: boolean;
  awards: AwardProposalItem[];
};

export type InputOfAwardProposalOutput = {
  search_limited: boolean;
  awards: InputOfAwardProposalItem[];
};

export type Ballot = {
  public_id: string;
  project: string;
  comment?: string;
  responses: BallotResponse[];
  submitted_at: string;
};

export type InputOfBallot = {
  comment?: string;
  responses: InputOfBallotResponse[];
};

export type BallotDraft = {
  public_id: string;
  project: string;
  responses?: unknown;
  comment?: string;
  updated_at: string;
};

export type InputOfBallotDraft = { responses?: unknown; comment?: string };

export type BallotDraftInputSchema = { responses?: unknown; comment?: string };

export type InputOfBallotDraftInputSchema = {
  responses?: unknown;
  comment?: string;
};

export type BallotResponse = { criterion_id: string; score: number };

export type InputOfBallotResponse = { criterion_id: string; score: number };

export type BallotSubmitInputSchema = {
  project: string;
  comment?: string;
  responses: BallotResponse[];
};

export type InputOfBallotSubmitInputSchema = {
  project: string;
  comment?: string;
  responses: InputOfBallotResponse[];
};

export type BasePrize = {
  public_id: string;
  name: string;
  description?: string;
  kind: BasePrizeKind;
  amount?: string | null;
  currency?: string;
  track?: string | null;
  position?: number;
};

export type InputOfBasePrize = {
  name: string;
  description?: string;
  kind: InputOfBasePrizeKind;
  amount?: string | null;
  currency?: string;
  track?: string | null;
  position?: number;
};

export type BasePrizeKind =
  | "cash"
  | "credit"
  | "discount"
  | "subscription"
  | "hardware"
  | "travel"
  | "service"
  | "mentorship"
  | "swag"
  | "other";

export type InputOfBasePrizeKind =
  | "cash"
  | "credit"
  | "discount"
  | "subscription"
  | "hardware"
  | "travel"
  | "service"
  | "mentorship"
  | "swag"
  | "other";

export type BulkOperationAction =
  "assign" | "advance" | "extend" | "move" | "send";

export type InputOfBulkOperationAction =
  "assign" | "advance" | "extend" | "move" | "send";

export type BulkOperationInput = {
  action: BulkOperationAction;
  plan?: string;
  coverage?: number;
  stage?: string;
  to_stage?: string;
  entries?: string[];
  gates?: string[];
  seconds?: number;
  projects?: string[];
  track?: string;
  subject?: string;
  body?: string;
  audience_kind?: string;
  audience_params?: Record<string, unknown>;
};

export type InputOfBulkOperationInput = {
  action: InputOfBulkOperationAction;
  plan?: string;
  coverage?: number;
  stage?: string;
  to_stage?: string;
  entries?: string[];
  gates?: string[];
  seconds?: number;
  projects?: string[];
  track?: string;
  subject?: string;
  body?: string;
  audience_kind?: string;
  audience_params?: Record<string, unknown>;
};

export type BulkRequest = {
  operations: BulkOperationInput[];
  preview_token?: string;
};

export type InputOfBulkRequest = {
  operations: InputOfBulkOperationInput[];
  preview_token?: string;
};

export type BulkResponse = {
  applied: boolean;
  effects: unknown[];
  preview_token?: string;
  expires_in?: number;
};

export type InputOfBulkResponse = {
  applied: boolean;
  effects: unknown[];
  preview_token?: string;
  expires_in?: number;
};

export type COIRelationshipKind = "team" | "institution" | "domain";

export type InputOfCOIRelationshipKind = "team" | "institution" | "domain";

export type COIRuleInputSchema = { kind: COIRuleKind; enabled: boolean };

export type InputOfCOIRuleInputSchema = {
  kind: InputOfCOIRuleKind;
  enabled: boolean;
};

export type COIRuleKind =
  "team_membership" | "project_membership" | "project_creator";

export type InputOfCOIRuleKind =
  "team_membership" | "project_membership" | "project_creator";

export type COIRuleOutputSchema = { kind: COIRuleKind; enabled: boolean };

export type InputOfCOIRuleOutputSchema = {
  kind: InputOfCOIRuleKind;
  enabled: boolean;
};

export type CalendarAssignmentSchema = {
  stage_name: string;
  plan: string;
  plan_name: string;
  rubric_published: boolean;
  assigned_count: number;
  submitted_count: number;
  completion_ratio: number | null;
};

export type InputOfCalendarAssignmentSchema = {
  stage_name: string;
  plan: string;
  plan_name: string;
  rubric_published: boolean;
  assigned_count: number;
  submitted_count: number;
  completion_ratio: number | null;
};

export type CalendarWindowSchema = {
  name: string;
  opens_at: string | null;
  closes_at: string | null;
  status: CalendarWindowSchemaStatusEnum;
};

export type InputOfCalendarWindowSchema = {
  name: string;
  opens_at: string | null;
  closes_at: string | null;
  status: InputOfCalendarWindowSchemaStatusEnum;
};

export type CalendarWindowSchemaStatusEnum = "not_yet_open" | "open" | "closed";

export type InputOfCalendarWindowSchemaStatusEnum =
  "not_yet_open" | "open" | "closed";

export type CalibrationCriterionSummarySchema = {
  criterion_id: string;
  scores: Record<string, number>;
  min: number;
  max: number;
  mean: number;
  spread: number;
};

export type InputOfCalibrationCriterionSummarySchema = {
  criterion_id: string;
  scores: Record<string, number>;
  min: number;
  max: number;
  mean: number;
  spread: number;
};

export type CalibrationOverviewSchema = {
  required: boolean;
  project_count: number;
  judges_total: number;
  judges_complete: number;
};

export type InputOfCalibrationOverviewSchema = {
  required: boolean;
  project_count: number;
  judges_total: number;
  judges_complete: number;
};

export type CalibrationProjectItemSchema = { project: string; name: string };

export type InputOfCalibrationProjectItemSchema = {
  project: string;
  name: string;
};

export type CalibrationProjectSummarySchema = {
  project: string;
  project_name: string;
  criteria: CalibrationCriterionSummarySchema[];
};

export type InputOfCalibrationProjectSummarySchema = {
  project: string;
  project_name: string;
  criteria: InputOfCalibrationCriterionSummarySchema[];
};

export type CalibrationProjectsInputSchema = { projects: string[] };

export type InputOfCalibrationProjectsInputSchema = { projects: string[] };

export type CalibrationStatusSchema = {
  required: boolean;
  total: number;
  completed: string[];
  remaining: string[];
  is_complete: boolean;
};

export type InputOfCalibrationStatusSchema = {
  required: boolean;
  total: number;
  completed: string[];
  remaining: string[];
  is_complete: boolean;
};

export type CandidateOutput = {
  public_id: string;
  name: string;
  track: string | null;
  has_finalized_submission: boolean;
};

export type InputOfCandidateOutput = {
  public_id: string;
  name: string;
  track: string | null;
  has_finalized_submission: boolean;
};

export type CandidateQueueItemSchema = {
  project: string;
  name: string;
  status: CandidateQueueStatus;
};

export type InputOfCandidateQueueItemSchema = {
  project: string;
  name: string;
  status: InputOfCandidateQueueStatus;
};

export type CandidateQueueStatus = "pending" | "drafted" | "submitted";

export type InputOfCandidateQueueStatus = "pending" | "drafted" | "submitted";

export type CandidateSchema = { project: string; name: string };

export type InputOfCandidateSchema = { project: string; name: string };

export type CandidateTypeEnum = "project";

export type InputOfCandidateTypeEnum = "project";

export type CategoryEnum =
  "contrast" | "heading" | "accessible-name" | "keyboard";

export type InputOfCategoryEnum =
  "contrast" | "heading" | "accessible-name" | "keyboard";

export type ChallengeOutput = {
  public_id: string;
  name: string;
  description: string;
  eligibility_track: string | null;
  components: ComponentOutput[];
  resources: ResourceOutput[];
};

export type InputOfChallengeOutput = {
  public_id: string;
  name: string;
  description: string;
  eligibility_track: string | null;
  components: InputOfComponentOutput[];
  resources: InputOfResourceOutput[];
};

export type CheckIn = {
  public_id: string;
  participant: string;
  participant_username: string;
  checked_in_by: string;
  checked_in_at: string;
};

export type InputOfCheckIn = {};

export type CheckInInputSchema = { participant: string };

export type InputOfCheckInInputSchema = { participant: string };

export type ChecklistItemSchema = {
  id: string;
  severity: string;
  passed: boolean;
  detail: string;
};

export type InputOfChecklistItemSchema = {
  id: string;
  severity: string;
  passed: boolean;
  detail: string;
};

export type CloneInput = { name: string; slug: string; sections?: string[] };

export type InputOfCloneInput = {
  name: string;
  slug: string;
  sections?: string[];
};

export type CloseCallsSchema = {
  normalization_run: number | null;
  projects: string[];
};

export type InputOfCloseCallsSchema = {
  normalization_run: number | null;
  projects: string[];
};

export type CloseInput = { state: CloseInputStateEnum; note?: string };

export type InputOfCloseInput = {
  state: InputOfCloseInputStateEnum;
  note?: string;
};

export type CloseInputStateEnum = "resolved" | "waived";

export type InputOfCloseInputStateEnum = "resolved" | "waived";

export type Comment = {
  public_id: string;
  author: string;
  body: string;
  created_at: string;
  hidden_at: string | null;
};

export type InputOfComment = { body: string };

export type CommentVisibilityEnum =
  "organizer" | "organizer_judge" | "everyone";

export type InputOfCommentVisibilityEnum =
  "organizer" | "organizer_judge" | "everyone";

export type CommunityAuditSchema = {
  public_id: string;
  actor: string | null;
  action: string;
  detail: string;
  created_at: string;
};

export type InputOfCommunityAuditSchema = {
  public_id: string;
  actor: string | null;
  action: string;
  detail: string;
  created_at: string;
};

export type ComponentInput = {
  kind: BasePrizeKind;
  name: string;
  description?: string;
  quantity: number;
  amount?: string | null;
  currency?: string;
};

export type InputOfComponentInput = {
  kind: InputOfBasePrizeKind;
  name: string;
  description?: string;
  quantity: number;
  amount?: string | null;
  currency?: string;
};

export type ComponentOutput = {
  public_id: string;
  kind: string;
  name: string;
  description: string;
  quantity: number;
  amount: string | null;
  currency: string;
};

export type InputOfComponentOutput = {
  public_id: string;
  kind: string;
  name: string;
  description: string;
  quantity: number;
  amount: string | null;
  currency: string;
};

export type ConfigHistoryEntrySchema = {
  public_id: string;
  actor: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  changes: unknown;
  created_at: string;
};

export type InputOfConfigHistoryEntrySchema = {
  public_id: string;
  actor: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  changes: unknown;
  created_at: string;
};

export type ConfigRestoreResultSchema = {
  restored: boolean;
  resource_type: string;
  resource_id: string;
  changes: unknown;
};

export type InputOfConfigRestoreResultSchema = {
  restored: boolean;
  resource_type: string;
  resource_id: string;
  changes: unknown;
};

export type ConflictOfInterest = {
  public_id: string;
  judge: string;
  project: string;
  reason?: string;
  created_at: string;
};

export type InputOfConflictOfInterest = { reason?: string };

export type ConformanceReportOutput = {
  event: string;
  generated_at: string;
  conformance_claimed: boolean;
  standard: string;
  theme: Record<string, unknown>;
  summary: Record<string, number>;
  pages: Record<string, unknown>[];
  manual_review: Record<string, unknown>[];
};

export type InputOfConformanceReportOutput = {
  event: string;
  generated_at: string;
  conformance_claimed: boolean;
  standard: string;
  theme: Record<string, unknown>;
  summary: Record<string, number>;
  pages: Record<string, unknown>[];
  manual_review: Record<string, unknown>[];
};

export type CreateTeamInput = { name: string };

export type InputOfCreateTeamInput = { name: string };

export type CreateTeamInviteInput = { max_uses?: number };

export type InputOfCreateTeamInviteInput = { max_uses?: number };

export type CredentialCreateSchema = {
  name: string;
  allowed_actions: string[];
  event?: string | null;
  expires_in_days?: number;
};

export type InputOfCredentialCreateSchema = {
  name: string;
  allowed_actions: string[];
  event?: string | null;
  expires_in_days?: number;
};

export type CredentialIssuedSchema = {
  public_id: string;
  name: string;
  workspace: string;
  event: string | null;
  allowed_actions: string[];
  created_at: string;
  expires_at: string;
  revoked_at: string | null;
  token: string;
};

export type InputOfCredentialIssuedSchema = {
  public_id: string;
  name: string;
  workspace: string;
  event: string | null;
  allowed_actions: string[];
  created_at: string;
  expires_at: string;
  revoked_at: string | null;
  token: string;
};

export type CredentialReadSchema = {
  public_id: string;
  name: string;
  workspace: string;
  event: string | null;
  allowed_actions: string[];
  created_at: string;
  expires_at: string;
  revoked_at: string | null;
};

export type InputOfCredentialReadSchema = {
  public_id: string;
  name: string;
  workspace: string;
  event: string | null;
  allowed_actions: string[];
  created_at: string;
  expires_at: string;
  revoked_at: string | null;
};

export type DecisionInput = {
  decision: DecisionInputDecisionEnum;
  note?: string;
};

export type InputOfDecisionInput = {
  decision: InputOfDecisionInputDecisionEnum;
  note?: string;
};

export type DecisionInputDecisionEnum =
  "pending" | "needs_remediation" | "cleared" | "ineligible";

export type InputOfDecisionInputDecisionEnum =
  "pending" | "needs_remediation" | "cleared" | "ineligible";

export type DecisionNoteInput = { note?: string };

export type InputOfDecisionNoteInput = { note?: string };

export type DeliveryInspection = {
  public_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempts: number;
  last_status_code: number | null;
  last_error: string;
  next_attempt_at: string | null;
  created_at: string;
  completed_at: string | null;
  destination: string;
  next_body: string;
  body_sha256: string;
  signature_scheme: string;
  history: AttemptOutput[];
  history_has_more: boolean;
};

export type InputOfDeliveryInspection = {
  public_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempts: number;
  last_status_code: number | null;
  last_error: string;
  next_attempt_at: string | null;
  created_at: string;
  completed_at: string | null;
  destination: string;
  next_body: string;
  body_sha256: string;
  signature_scheme: string;
  history: InputOfAttemptOutput[];
  history_has_more: boolean;
};

export type DeliveryOutput = {
  public_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempts: number;
  last_status_code: number | null;
  last_error: string;
  next_attempt_at: string | null;
  created_at: string;
  completed_at: string | null;
};

export type InputOfDeliveryOutput = {
  public_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempts: number;
  last_status_code: number | null;
  last_error: string;
  next_attempt_at: string | null;
  created_at: string;
  completed_at: string | null;
};

export type DispositionEnum =
  | "dismiss"
  | "escalate"
  | "resolve"
  | "hide"
  | "acknowledge"
  | "approve"
  | "reject"
  | "waitlist";

export type InputOfDispositionEnum =
  | "dismiss"
  | "escalate"
  | "resolve"
  | "hide"
  | "acknowledge"
  | "approve"
  | "reject"
  | "waitlist";

export type DropoutCoverageGapSchema = { project: string; missing: number };

export type InputOfDropoutCoverageGapSchema = {
  project: string;
  missing: number;
};

export type DropoutScenarioSchema = {
  drop_judges: string[];
  evidence: Record<string, unknown>;
  pending_removed: number;
  assignments_added: number;
  coverage_gaps: DropoutCoverageGapSchema[];
};

export type InputOfDropoutScenarioSchema = {
  drop_judges: string[];
  evidence: Record<string, unknown>;
  pending_removed: number;
  assignments_added: number;
  coverage_gaps: InputOfDropoutCoverageGapSchema[];
};

export type DropoutSimulationInputSchema = { drop_scenarios: string[][] };

export type InputOfDropoutSimulationInputSchema = {
  drop_scenarios: string[][];
};

export type DropoutSimulationSchema = {
  active_version: string;
  baseline: Record<string, unknown>;
  scenarios: DropoutScenarioSchema[];
};

export type InputOfDropoutSimulationSchema = {
  active_version: string;
  baseline: Record<string, unknown>;
  scenarios: InputOfDropoutScenarioSchema[];
};

export type EmailTokenInputSchema = { email: string };

export type InputOfEmailTokenInputSchema = { email: string };

export type EmailTokenReceiptSchema = { token: string; expires_at: string };

export type InputOfEmailTokenReceiptSchema = {
  token: string;
  expires_at: string;
};

export type ErrorSchema = { detail: string };

export type InputOfErrorSchema = { detail: string };

export type EvaluationPlan = {
  public_id: string;
  name: string;
  candidate_type?: CandidateTypeEnum;
  pool_strategy?: PoolStrategyEnum;
  mode?: EvaluationPlanModeEnum;
  results_visible_to_participants?: boolean;
  feedback_visible_to_participants?: boolean;
  feedback_anonymous?: boolean;
  draft_criteria?: unknown;
  pool?: string | null;
  hybrid_source?: string | null;
  current_rubric_version: number | null;
  active_assignment_version: number | null;
  published_normalization_run: number | null;
  published_pairwise_run: number | null;
  calibration_projects: string[];
  calibration_required?: boolean;
  blind_judging?: boolean;
  prize_judging?: boolean;
  created_at: string;
  updated_at: string;
};

export type InputOfEvaluationPlan = {
  name: string;
  candidate_type?: InputOfCandidateTypeEnum;
  pool_strategy?: InputOfPoolStrategyEnum;
  mode?: InputOfEvaluationPlanModeEnum;
  results_visible_to_participants?: boolean;
  feedback_visible_to_participants?: boolean;
  feedback_anonymous?: boolean;
  draft_criteria?: unknown;
  pool?: string | null;
  hybrid_source?: string | null;
  calibration_required?: boolean;
  blind_judging?: boolean;
  prize_judging?: boolean;
};

export type EvaluationPlanModeEnum = "rubric" | "pairwise";

export type InputOfEvaluationPlanModeEnum = "rubric" | "pairwise";

export type EvaluationPool = {
  public_id: string;
  name: string;
  created_at: string;
};

export type InputOfEvaluationPool = { name: string };

export type EvaluationProgressSchema = {
  candidate_count: number;
  pool_judge_count: number;
  conflict_count: number;
  expected_ballots: number | null;
  submitted_ballots: number;
  completion_ratio: number | null;
  rubric_published: boolean;
  assignment_active: boolean;
  latest_normalization_run: NormalizationProgressSchema | null;
  results_published: boolean;
  calibration: CalibrationOverviewSchema | null;
};

export type InputOfEvaluationProgressSchema = {
  candidate_count: number;
  pool_judge_count: number;
  conflict_count: number;
  expected_ballots: number | null;
  submitted_ballots: number;
  completion_ratio: number | null;
  rubric_published: boolean;
  assignment_active: boolean;
  latest_normalization_run: InputOfNormalizationProgressSchema | null;
  results_published: boolean;
  calibration: InputOfCalibrationOverviewSchema | null;
};

export type Event = {
  public_id: string;
  name: string;
  slug: string;
  description?: string;
  timezone?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  status: EventStatus;
  is_public?: boolean;
  created_at: string;
  updated_at: string;
};

export type InputOfEvent = {
  name: string;
  slug: string;
  description?: string;
  timezone?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  is_public?: boolean;
};

export type EventAnalyticsResponse = {
  event: string;
  generated_at: string;
  registration: unknown;
  teams: unknown;
  submissions: unknown;
  judging: unknown;
  voting: unknown;
};

export type InputOfEventAnalyticsResponse = {
  event: string;
  generated_at: string;
  registration: unknown;
  teams: unknown;
  submissions: unknown;
  judging: unknown;
  voting: unknown;
};

export type EventApplication = {
  public_id: string;
  user: string;
  username: string;
  status: EventApplicationStatusEnum;
  note: string;
  waitlist_position: number | null;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
};

export type InputOfEventApplication = {};

export type EventApplicationStatusEnum =
  "pending" | "approved" | "waitlisted" | "rejected";

export type InputOfEventApplicationStatusEnum =
  "pending" | "approved" | "waitlisted" | "rejected";

export type EventAsCodeApplyInput = {
  document: unknown;
  prune?: boolean;
  expected_digest: string;
};

export type InputOfEventAsCodeApplyInput = {
  document: unknown;
  prune?: boolean;
  expected_digest: string;
};

export type EventAsCodeDocumentInput = { document: unknown; prune?: boolean };

export type InputOfEventAsCodeDocumentInput = {
  document: unknown;
  prune?: boolean;
};

export type EventDashboardSchema = {
  event: Event;
  track_count: number;
  base_prize_count: number;
  configuration_checks: string[];
};

export type InputOfEventDashboardSchema = {
  event: InputOfEvent;
  track_count: number;
  base_prize_count: number;
  configuration_checks: string[];
};

export type EventQuestionStatus = "pending" | "published" | "hidden";

export type InputOfEventQuestionStatus = "pending" | "published" | "hidden";

export type EventStatus = "draft" | "open" | "closed" | "archived";

export type InputOfEventStatus = "draft" | "open" | "closed" | "archived";

export type EventStatusInput = { status: EventStatus };

export type InputOfEventStatusInput = { status: InputOfEventStatus };

export type EventTemplateCreateInput = {
  event: string;
  name: string;
  sections?: string[];
};

export type InputOfEventTemplateCreateInput = {
  event: string;
  name: string;
  sections?: string[];
};

export type EventTemplateOutput = {
  public_id: string;
  name: string;
  source_event_name: string;
  sections: string[];
  created_at: string;
};

export type InputOfEventTemplateOutput = {
  public_id: string;
  name: string;
  source_event_name: string;
  sections: string[];
  created_at: string;
};

export type ExceptionApprovalInput = { note?: string; expires_at?: string };

export type InputOfExceptionApprovalInput = {
  note?: string;
  expires_at?: string;
};

export type ExceptionGrant = {
  public_id: string;
  action: ActionEnum;
  subject_type: string;
  subject_id: string;
  scope?: string;
  reason?: string;
  granted_at: string;
  expires_at?: string | null;
};

export type InputOfExceptionGrant = {
  action: InputOfActionEnum;
  subject_type: string;
  subject_id: string;
  scope?: string;
  reason?: string;
  expires_at?: string | null;
};

export type ExceptionRequestInput = { reason: string };

export type InputOfExceptionRequestInput = { reason: string };

export type ExpertiseInputSchema = { tags: string[] };

export type InputOfExpertiseInputSchema = { tags: string[] };

export type ExpertiseOutputSchema = {
  judge: string;
  tags: string[];
  updated_at: string | null;
};

export type InputOfExpertiseOutputSchema = {
  judge: string;
  tags: string[];
  updated_at: string | null;
};

export type ExternalArtifactInputSchema = {
  kind: string;
  visibility: string;
  title?: string;
  external_url: string;
};

export type InputOfExternalArtifactInputSchema = {
  kind: string;
  visibility: string;
  title?: string;
  external_url: string;
};

export type FeedbackEntrySchema = {
  judge: string | null;
  comment: string;
  submitted_at: string;
};

export type InputOfFeedbackEntrySchema = {
  judge: string | null;
  comment: string;
  submitted_at: string;
};

export type FinalizeInput = { winners: string[]; override_reason?: string };

export type InputOfFinalizeInput = {
  winners: string[];
  override_reason?: string;
};

export type FindingInput = { message: string; severity?: SeverityEnum };

export type InputOfFindingInput = {
  message: string;
  severity?: InputOfSeverityEnum;
};

export type FindingOutput = {
  public_id: string;
  code: string;
  automated: boolean;
  severity: string;
  message: string;
  state: string;
  participant_response: string;
  resolution_note: string;
  opened_at: string;
  addressed_at: string | null;
  closed_at: string | null;
};

export type InputOfFindingOutput = {
  public_id: string;
  code: string;
  automated: boolean;
  severity: string;
  message: string;
  state: string;
  participant_response: string;
  resolution_note: string;
  opened_at: string;
  addressed_at: string | null;
  closed_at: string | null;
};

export type FormAnswersInputSchema = { answers: unknown };

export type InputOfFormAnswersInputSchema = { answers: unknown };

export type FormDraftInputSchema = { schema: unknown };

export type InputOfFormDraftInputSchema = { schema: unknown };

export type FormNameInputSchema = { name: string };

export type InputOfFormNameInputSchema = { name: string };

export type FormPayloadSchema = {
  public_id: string;
  name: string;
  stage: string | null;
  draft_schema: unknown;
};

export type InputOfFormPayloadSchema = {
  public_id: string;
  name: string;
  stage: string | null;
  draft_schema: unknown;
};

export type FormResponseSchema = { version: string; answers: unknown };

export type InputOfFormResponseSchema = { version: string; answers: unknown };

export type FormVersionSchema = {
  public_id: string;
  number: number;
  schema: unknown;
  published_at: string;
};

export type InputOfFormVersionSchema = {
  public_id: string;
  number: number;
  schema: unknown;
  published_at: string;
};

export type FulfillmentInputStateEnum =
  "pending" | "contacted" | "verified" | "sent" | "claimed" | "failed";

export type InputOfFulfillmentInputStateEnum =
  "pending" | "contacted" | "verified" | "sent" | "claimed" | "failed";

export type FulfillmentOutput = {
  public_id: string;
  component: string;
  component_name: string;
  state: string;
  note: string;
  updated_at: string;
};

export type InputOfFulfillmentOutput = {
  public_id: string;
  component: string;
  component_name: string;
  state: string;
  note: string;
  updated_at: string;
};

export type GalleryItemOutput = {
  public_id: string;
  name: string;
  description: string;
  track: string | null;
  team: string | null;
  url: string;
};

export type InputOfGalleryItemOutput = {
  public_id: string;
  name: string;
  description: string;
  track: string | null;
  team: string | null;
  url: string;
};

export type GalleryProjectSchema = {
  id: string;
  title: string;
  summary: string;
  team: string;
  track: string;
  repo_url: string;
};

export type InputOfGalleryProjectSchema = {
  id: string;
  title: string;
  summary: string;
  team: string;
  track: string;
  repo_url: string;
};

export type GraphValidationSchema = {
  valid: boolean;
  order?: string[];
  errors?: string[];
};

export type InputOfGraphValidationSchema = {
  valid: boolean;
  order?: string[];
  errors?: string[];
};

export type HealthResponse = { status: string };

export type InputOfHealthResponse = { status: string };

export type IdentityModeEnum = "authenticated" | "email_link" | "token";

export type InputOfIdentityModeEnum = "authenticated" | "email_link" | "token";

export type ImportedEventOutput = {
  public_id: string;
  name: string;
  slug: string;
};

export type InputOfImportedEventOutput = {
  public_id: string;
  name: string;
  slug: string;
};

export type InboxMessageSchema = {
  public_id: string;
  subject: string;
  body: string;
  event: string;
  event_name: string;
  created_at: string;
  read_at: string | null;
};

export type InputOfInboxMessageSchema = {
  public_id: string;
  subject: string;
  body: string;
  event: string;
  event_name: string;
  created_at: string;
  read_at: string | null;
};

export type InstantiateInput = { name: string; slug: string };

export type InputOfInstantiateInput = { name: string; slug: string };

export type JudgeCOIRelationship = {
  public_id: string;
  judge: string;
  kind: COIRelationshipKind;
  team: string | null;
  value?: string;
  declared_by: string;
  created_at: string;
};

export type InputOfJudgeCOIRelationship = {
  kind: InputOfCOIRelationshipKind;
  value?: string;
};

export type JudgeCOIRelationshipInputSchema = {
  judge?: string;
  kind: COIRelationshipKind;
  team?: string;
  value?: string;
};

export type InputOfJudgeCOIRelationshipInputSchema = {
  judge?: string;
  kind: InputOfCOIRelationshipKind;
  team?: string;
  value?: string;
};

export type JudgeCalendarSchema = {
  windows: CalendarWindowSchema[];
  assignments: CalendarAssignmentSchema[];
};

export type InputOfJudgeCalendarSchema = {
  windows: InputOfCalendarWindowSchema[];
  assignments: InputOfCalendarAssignmentSchema[];
};

export type JudgeDirectorySchema = { judge: string; username: string };

export type InputOfJudgeDirectorySchema = { judge: string; username: string };

export type JudgeEventSummary = { public_id: string; name: string };

export type InputOfJudgeEventSummary = { public_id: string; name: string };

export type JudgeInvitationDecisionSchema = {
  decision: JudgeInvitationDecisionSchemaDecisionEnum;
};

export type InputOfJudgeInvitationDecisionSchema = {
  decision: InputOfJudgeInvitationDecisionSchemaDecisionEnum;
};

export type JudgeInvitationDecisionSchemaDecisionEnum = "accept" | "decline";

export type InputOfJudgeInvitationDecisionSchemaDecisionEnum =
  "accept" | "decline";

export type JudgeInvitationInputSchema = { pool: string; judge: string };

export type InputOfJudgeInvitationInputSchema = { pool: string; judge: string };

export type JudgeInvitationSchema = {
  public_id: string;
  event: string;
  event_name: string;
  pool: string;
  pool_name: string;
  judge: string;
  judge_username: string;
  status: JudgeInvitationSchemaStatusEnum;
  created_at: string;
  responded_at: string | null;
};

export type InputOfJudgeInvitationSchema = {
  public_id: string;
  event: string;
  event_name: string;
  pool: string;
  pool_name: string;
  judge: string;
  judge_username: string;
  status: InputOfJudgeInvitationSchemaStatusEnum;
  created_at: string;
  responded_at: string | null;
};

export type JudgeInvitationSchemaStatusEnum =
  "pending" | "accepted" | "declined" | "revoked";

export type InputOfJudgeInvitationSchemaStatusEnum =
  "pending" | "accepted" | "declined" | "revoked";

export type JudgeRecordInput = { user: string };

export type InputOfJudgeRecordInput = { user: string };

export type JudgeScoreSchema = {
  project: string;
  comment: string;
  criteria: Record<string, number>;
};

export type InputOfJudgeScoreSchema = {
  project: string;
  comment: string;
  criteria: Record<string, number>;
};

export type JudgeSuggestionSchema = {
  rank: number;
  judge: string;
  username: string;
  expertise_tags: string[];
  matched_tags: string[];
  events_judged: number;
  ballots_completed: number;
  assignments_received: number;
  completion_rate: number | null;
};

export type InputOfJudgeSuggestionSchema = {
  rank: number;
  judge: string;
  username: string;
  expertise_tags: string[];
  matched_tags: string[];
  events_judged: number;
  ballots_completed: number;
  assignments_received: number;
  completion_rate: number | null;
};

export type JudgeWorkloadRowSchema = {
  judge: string;
  assigned_count: number;
  submitted_count: number;
  completion_ratio: number;
};

export type InputOfJudgeWorkloadRowSchema = {
  judge: string;
  assigned_count: number;
  submitted_count: number;
  completion_ratio: number;
};

export type LaunchChecklistSchema = {
  status: string;
  items: ChecklistItemSchema[];
};

export type InputOfLaunchChecklistSchema = {
  status: string;
  items: InputOfChecklistItemSchema[];
};

export type LibraryTemplateOutput = {
  slug: string;
  label: string;
  description: string;
  tracks: string[];
  stages: string[];
};

export type InputOfLibraryTemplateOutput = {
  slug: string;
  label: string;
  description: string;
  tracks: string[];
  stages: string[];
};

export type LocationInput = {
  kind: LocationKind;
  name: string;
  parent?: string | null;
  capacity?: number | null;
  x?: number | null;
  y?: number | null;
  notes?: string;
  position?: number;
};

export type InputOfLocationInput = {
  kind: InputOfLocationKind;
  name: string;
  parent?: string | null;
  capacity?: number | null;
  x?: number | null;
  y?: number | null;
  notes?: string;
  position?: number;
};

export type LocationKind = "room" | "table" | "booth";

export type InputOfLocationKind = "room" | "table" | "booth";

export type LocationOutput = {
  public_id: string;
  kind: string;
  name: string;
  parent: string | null;
  capacity: number | null;
  x: number | null;
  y: number | null;
  notes: string;
  position: number;
  assigned: number;
};

export type InputOfLocationOutput = {
  public_id: string;
  kind: string;
  name: string;
  parent: string | null;
  capacity: number | null;
  x: number | null;
  y: number | null;
  notes: string;
  position: number;
  assigned: number;
};

export type LoginInputSchema = { username: string; password: string };

export type InputOfLoginInputSchema = { username: string; password: string };

export type LoginResponseSchema = { user: UserSummarySchema };

export type InputOfLoginResponseSchema = { user: InputOfUserSummarySchema };

export type MarketplaceProfileInput = {
  skills: string[];
  roles?: string[];
  interests?: string[];
  availability_hours_per_week?: number | null;
  bio?: string;
  visible: boolean;
};

export type InputOfMarketplaceProfileInput = {
  skills: string[];
  roles?: string[];
  interests?: string[];
  availability_hours_per_week?: number | null;
  bio?: string;
  visible: boolean;
};

export type MarketplaceProfileSchema = {
  public_id: string;
  user: string;
  username: string;
  skills: string[];
  roles: string[];
  interests: string[];
  availability_hours_per_week: number | null;
  bio: string;
  visible: boolean;
  matched_skills?: string[];
  matched_roles?: string[];
  matched_interests?: string[];
  availability_compatible?: boolean | null;
};

export type InputOfMarketplaceProfileSchema = {
  public_id: string;
  user: string;
  username: string;
  skills: string[];
  roles: string[];
  interests: string[];
  availability_hours_per_week: number | null;
  bio: string;
  visible: boolean;
  matched_skills?: string[];
  matched_roles?: string[];
  matched_interests?: string[];
  availability_compatible?: boolean | null;
};

export type MembershipInputSchema = { username: string; role: string };

export type InputOfMembershipInputSchema = { username: string; role: string };

export type MembershipSchema = {
  public_id: string;
  user: string;
  role: string;
};

export type InputOfMembershipSchema = {
  public_id: string;
  user: string;
  role: string;
};

export type MembershipSummarySchema = {
  workspace: string;
  workspace_name: string;
  workspace_slug: string;
  role: string;
};

export type InputOfMembershipSummarySchema = {
  workspace: string;
  workspace_name: string;
  workspace_slug: string;
  role: string;
};

export type MentorNote = {
  public_id: string;
  mentor: string;
  mentor_username: string;
  body: string;
  created_at: string;
};

export type InputOfMentorNote = { body: string };

export type MentorNoteInputSchema = { body: string };

export type InputOfMentorNoteInputSchema = { body: string };

export type MessageInputSchema = {
  subject: string;
  body: string;
  audience_kind: string;
  audience_params?: unknown;
};

export type InputOfMessageInputSchema = {
  subject: string;
  body: string;
  audience_kind: string;
  audience_params?: unknown;
};

export type MessageSchema = {
  public_id: string;
  subject: string;
  body: string;
  audience_kind: string;
  audience_params: unknown;
  recipient_count: number;
  email_failure_count: number;
  created_at: string;
};

export type InputOfMessageSchema = {
  public_id: string;
  subject: string;
  body: string;
  audience_kind: string;
  audience_params: unknown;
  recipient_count: number;
  email_failure_count: number;
  created_at: string;
};

export type MethodEnum = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type InputOfMethodEnum = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type ModerationQueueResponse = { sections: unknown[] };

export type InputOfModerationQueueResponse = { sections: unknown[] };

export type ModerationReviewInput = {
  kind: ModerationReviewInputKindEnum;
  source_key: string;
  evidence_digest: string;
  disposition: DispositionEnum;
  note: string;
};

export type InputOfModerationReviewInput = {
  kind: InputOfModerationReviewInputKindEnum;
  source_key: string;
  evidence_digest: string;
  disposition: InputOfDispositionEnum;
  note: string;
};

export type ModerationReviewInputKindEnum =
  "duplicate" | "voting" | "content" | "artifact" | "eligibility";

export type InputOfModerationReviewInputKindEnum =
  "duplicate" | "voting" | "content" | "artifact" | "eligibility";

export type ModerationReviewResponse = {
  public_id: string;
  kind: string;
  source_key: string;
  evidence_digest: string;
  evidence: unknown;
  disposition: string;
  note: string;
  actor: string;
  created_at: string;
};

export type InputOfModerationReviewResponse = {
  public_id: string;
  kind: string;
  source_key: string;
  evidence_digest: string;
  evidence: unknown;
  disposition: string;
  note: string;
  actor: string;
  created_at: string;
};

export type MyEventApplicationResponse = {
  application: EventApplication | null;
};

export type InputOfMyEventApplicationResponse = {
  application: InputOfEventApplication | null;
};

export type MyMarketplaceProfileResponse = {
  profile: MarketplaceProfileSchema | null;
};

export type InputOfMyMarketplaceProfileResponse = {
  profile: InputOfMarketplaceProfileSchema | null;
};

export type MyTeamResponse = { team: Team | null; my_role: string | null };

export type InputOfMyTeamResponse = {
  team: InputOfTeam | null;
  my_role: string | null;
};

export type NormalizationInputSchema = { ridge_lambda?: number };

export type InputOfNormalizationInputSchema = { ridge_lambda?: number };

export type NormalizationProgressSchema = {
  number: number;
  converged: boolean;
  low_information_judges: number;
};

export type InputOfNormalizationProgressSchema = {
  number: number;
  converged: boolean;
  low_information_judges: number;
};

export type NormalizationRun = {
  public_id: string;
  number: number;
  ridge_lambda: number;
  iterations: number;
  converged: boolean;
  grand_mean: number;
  evidence: unknown;
  created_at: string;
};

export type InputOfNormalizationRun = {
  number: number;
  ridge_lambda: number;
  iterations: number;
  converged: boolean;
  grand_mean: number;
  evidence: unknown;
};

export type NoteInput = { body: string; project?: string };

export type InputOfNoteInput = { body: string; project?: string };

export type OidcConfigSchema = {
  enabled: boolean;
  provider_name?: string;
  login_url?: string;
};

export type InputOfOidcConfigSchema = {
  enabled: boolean;
  provider_name?: string;
  login_url?: string;
};

export type OpenInput = { quorum?: number };

export type InputOfOpenInput = { quorum?: number };

export type OperationsSummarySchema = {
  participants: unknown;
  submissions: unknown;
  judging: unknown;
  stages: unknown;
  publication: unknown;
  moderation: unknown;
};

export type InputOfOperationsSummarySchema = {
  participants: unknown;
  submissions: unknown;
  judging: unknown;
  stages: unknown;
  publication: unknown;
  moderation: unknown;
};

export type OperatorActivitySchema = {
  action: string;
  actor: string | null;
  target_type: string;
  target_id: string;
  created_at: string;
};

export type InputOfOperatorActivitySchema = {
  action: string;
  actor: string | null;
  target_type: string;
  target_id: string;
  created_at: string;
};

export type OperatorConsoleSchema = {
  event_total: number;
  events: OperatorEventSchema[];
  template_total: number;
  templates: OperatorTemplateSchema[];
  activity: OperatorActivitySchema[];
};

export type InputOfOperatorConsoleSchema = {
  event_total: number;
  events: InputOfOperatorEventSchema[];
  template_total: number;
  templates: InputOfOperatorTemplateSchema[];
  activity: InputOfOperatorActivitySchema[];
};

export type OperatorEventSchema = {
  public_id: string;
  name: string;
  status: string;
  is_public: boolean;
  updated_at: string;
  health: string;
  blocker_count: number;
  warning_count: number;
};

export type InputOfOperatorEventSchema = {
  public_id: string;
  name: string;
  status: string;
  is_public: boolean;
  updated_at: string;
  health: string;
  blocker_count: number;
  warning_count: number;
};

export type OperatorTemplateSchema = {
  public_id: string;
  name: string;
  source_event_name: string;
};

export type InputOfOperatorTemplateSchema = {
  public_id: string;
  name: string;
  source_event_name: string;
};

export type Page = {
  public_id: string;
  theme?: ThemeEnum;
  created_at: string;
  updated_at: string;
};

export type InputOfPage = { theme?: InputOfThemeEnum };

export type PageBlock = {
  public_id: string;
  kind: PageBlockKindEnum;
  position?: number;
  config?: unknown;
  created_at: string;
  updated_at: string;
};

export type InputOfPageBlock = {
  kind: InputOfPageBlockKindEnum;
  position?: number;
  config?: unknown;
};

export type PageBlockKindEnum =
  | "hero"
  | "tracks"
  | "prizes"
  | "schedule"
  | "sponsors"
  | "faq"
  | "resources"
  | "gallery"
  | "results"
  | "announcements"
  | "rich_text"
  | "cta";

export type InputOfPageBlockKindEnum =
  | "hero"
  | "tracks"
  | "prizes"
  | "schedule"
  | "sponsors"
  | "faq"
  | "resources"
  | "gallery"
  | "results"
  | "announcements"
  | "rich_text"
  | "cta";

export type PageBlockOrderInput = { block_ids: string[] };

export type InputOfPageBlockOrderInput = { block_ids: string[] };

export type PairwiseComparison = {
  public_id: string;
  judge: string;
  project_a: string;
  project_b: string;
  winner: string | null;
  submitted_at: string;
};

export type InputOfPairwiseComparison = {};

export type PairwiseComparisonInputSchema = {
  project_a: string;
  project_b: string;
  winner?: string | null;
};

export type InputOfPairwiseComparisonInputSchema = {
  project_a: string;
  project_b: string;
  winner?: string | null;
};

export type PairwiseNextPairSchema = { project_a: string; project_b: string };

export type InputOfPairwiseNextPairSchema = {
  project_a: string;
  project_b: string;
};

export type PairwiseRankedResultSchema = {
  rank: number;
  project: string | null;
  project_name: string | null;
  strength: number;
  win_count: number;
  comparison_count: number;
  tie_break: number | null;
};

export type InputOfPairwiseRankedResultSchema = {
  rank: number;
  project: string | null;
  project_name: string | null;
  strength: number;
  win_count: number;
  comparison_count: number;
  tie_break: number | null;
};

export type PairwiseResultsPublishInputSchema = {
  pairwise_run: string;
  tie_breaks?: Record<string, number>;
};

export type InputOfPairwiseResultsPublishInputSchema = {
  pairwise_run: string;
  tie_breaks?: Record<string, number>;
};

export type PairwiseRun = {
  public_id: string;
  number: number;
  prior_games: number;
  iterations: number;
  converged: boolean;
  evidence: unknown;
  created_at: string;
};

export type InputOfPairwiseRun = {
  number: number;
  prior_games: number;
  iterations: number;
  converged: boolean;
  evidence: unknown;
};

export type PairwiseRunInputSchema = { prior_games?: number };

export type InputOfPairwiseRunInputSchema = { prior_games?: number };

export type ParticipantEventSummary = { public_id: string; name: string };

export type InputOfParticipantEventSummary = {
  public_id: string;
  name: string;
};

export type ParticipantFormSchema = {
  public_id: string;
  name: string;
  stage: string | null;
  number: number;
  schema: unknown;
};

export type InputOfParticipantFormSchema = {
  public_id: string;
  name: string;
  stage: string | null;
  number: number;
  schema: unknown;
};

export type ParticipantRulesInput = { title: string; body: string };

export type InputOfParticipantRulesInput = { title: string; body: string };

export type ParticipationModeEnum =
  "individual" | "team_formation" | "team_locked";

export type InputOfParticipationModeEnum =
  "individual" | "team_formation" | "team_locked";

export type PatchedBasePrize = {
  public_id?: string;
  name?: string;
  description?: string;
  kind?: BasePrizeKind;
  amount?: string | null;
  currency?: string;
  track?: string | null;
  position?: number;
};

export type InputOfPatchedBasePrize = {
  name?: string;
  description?: string;
  kind?: InputOfBasePrizeKind;
  amount?: string | null;
  currency?: string;
  track?: string | null;
  position?: number;
};

export type PatchedEvaluationPlan = {
  public_id?: string;
  name?: string;
  candidate_type?: CandidateTypeEnum;
  pool_strategy?: PoolStrategyEnum;
  mode?: EvaluationPlanModeEnum;
  results_visible_to_participants?: boolean;
  feedback_visible_to_participants?: boolean;
  feedback_anonymous?: boolean;
  draft_criteria?: unknown;
  pool?: string | null;
  hybrid_source?: string | null;
  current_rubric_version?: number | null;
  active_assignment_version?: number | null;
  published_normalization_run?: number | null;
  published_pairwise_run?: number | null;
  calibration_projects?: string[];
  calibration_required?: boolean;
  blind_judging?: boolean;
  prize_judging?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type InputOfPatchedEvaluationPlan = {
  name?: string;
  candidate_type?: InputOfCandidateTypeEnum;
  pool_strategy?: InputOfPoolStrategyEnum;
  mode?: InputOfEvaluationPlanModeEnum;
  results_visible_to_participants?: boolean;
  feedback_visible_to_participants?: boolean;
  feedback_anonymous?: boolean;
  draft_criteria?: unknown;
  pool?: string | null;
  hybrid_source?: string | null;
  calibration_required?: boolean;
  blind_judging?: boolean;
  prize_judging?: boolean;
};

export type PatchedEvent = {
  public_id?: string;
  name?: string;
  slug?: string;
  description?: string;
  timezone?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  status?: EventStatus;
  is_public?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type InputOfPatchedEvent = {
  name?: string;
  slug?: string;
  description?: string;
  timezone?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  is_public?: boolean;
};

export type PatchedFulfillmentInput = {
  state?: FulfillmentInputStateEnum;
  note?: string;
};

export type InputOfPatchedFulfillmentInput = {
  state?: InputOfFulfillmentInputStateEnum;
  note?: string;
};

export type PatchedLocationPatchInput = {
  kind?: LocationKind;
  name?: string;
  parent?: string | null;
  capacity?: number | null;
  x?: number | null;
  y?: number | null;
  notes?: string;
  position?: number;
};

export type InputOfPatchedLocationPatchInput = {
  kind?: InputOfLocationKind;
  name?: string;
  parent?: string | null;
  capacity?: number | null;
  x?: number | null;
  y?: number | null;
  notes?: string;
  position?: number;
};

export type PatchedPage = {
  public_id?: string;
  theme?: ThemeEnum;
  created_at?: string;
  updated_at?: string;
};

export type InputOfPatchedPage = { theme?: InputOfThemeEnum };

export type PatchedPageBlock = {
  public_id?: string;
  kind?: PageBlockKindEnum;
  position?: number;
  config?: unknown;
  created_at?: string;
  updated_at?: string;
};

export type InputOfPatchedPageBlock = {
  kind?: InputOfPageBlockKindEnum;
  position?: number;
  config?: unknown;
};

export type PatchedPolicy = {
  public_id?: string;
  name?: string;
  ast?: unknown;
  preset?: string;
  preset_params?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type InputOfPatchedPolicy = {
  name?: string;
  ast?: unknown;
  preset?: string;
  preset_params?: Record<string, unknown>;
};

export type PatchedProjectPatchInputSchema = {
  name?: string;
  description?: string;
  track?: string | null;
};

export type InputOfPatchedProjectPatchInputSchema = {
  name?: string;
  description?: string;
  track?: string | null;
};

export type PatchedResourceInput = {
  kind?: ResourceInputKindEnum;
  title?: string;
  url?: string;
  body?: string;
  position?: number;
};

export type InputOfPatchedResourceInput = {
  kind?: InputOfResourceInputKindEnum;
  title?: string;
  url?: string;
  body?: string;
  position?: number;
};

export type PatchedStage = {
  public_id?: string;
  name?: string;
  position?: number;
  is_initial?: boolean;
  participation_mode?: ParticipationModeEnum;
  created_at?: string;
};

export type InputOfPatchedStage = {
  name?: string;
  position?: number;
  is_initial?: boolean;
  participation_mode?: InputOfParticipationModeEnum;
};

export type PatchedSubscriptionUpdate = { enabled?: boolean; url?: string };

export type InputOfPatchedSubscriptionUpdate = {
  enabled?: boolean;
  url?: string;
};

export type PatchedTaxonomyPatchInput = {
  name?: string;
  allows_multiple?: boolean;
  terms?: TermInput[];
};

export type InputOfPatchedTaxonomyPatchInput = {
  name?: string;
  allows_multiple?: boolean;
  terms?: InputOfTermInput[];
};

export type PatchedTeamOpeningInput = {
  title?: string;
  description?: string;
  desired_skills?: string[];
  desired_roles?: string[];
  interests?: string[];
  min_availability_hours_per_week?: number | null;
  project?: string | null;
  is_open?: boolean;
};

export type InputOfPatchedTeamOpeningInput = {
  title?: string;
  description?: string;
  desired_skills?: string[];
  desired_roles?: string[];
  interests?: string[];
  min_availability_hours_per_week?: number | null;
  project?: string | null;
  is_open?: boolean;
};

export type PatchedTemporalGate = {
  public_id?: string;
  name?: string;
  opens_at?: string | null;
  closes_at?: string | null;
  event_local_opens_at?: string | null;
  event_local_closes_at?: string | null;
  dst_warning?: string | null;
  created_at?: string;
};

export type InputOfPatchedTemporalGate = {
  name?: string;
  opens_at?: string | null;
  closes_at?: string | null;
};

export type PatchedTrack = {
  public_id?: string;
  name?: string;
  description?: string;
  position?: number;
};

export type InputOfPatchedTrack = {
  name?: string;
  description?: string;
  position?: number;
};

export type PatchedVotingPlan = {
  public_id?: string;
  identity_mode?: IdentityModeEnum;
  opens_at?: string;
  closes_at?: string;
  allow_comments?: boolean;
  comment_visibility?: CommentVisibilityEnum;
  results_published_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type InputOfPatchedVotingPlan = {
  identity_mode?: InputOfIdentityModeEnum;
  opens_at?: string;
  closes_at?: string;
  allow_comments?: boolean;
  comment_visibility?: InputOfCommentVisibilityEnum;
};

export type PermissionMatrixEntrySchema = {
  resource: string;
  view: string;
  path: string;
  method: string;
  access: AccessEnum;
  roles: string[];
  unrecognized: boolean;
};

export type InputOfPermissionMatrixEntrySchema = {
  resource: string;
  view: string;
  path: string;
  method: string;
  access: InputOfAccessEnum;
  roles: string[];
  unrecognized: boolean;
};

export type PlacementInput = { location: string | null };

export type InputOfPlacementInput = { location: string | null };

export type PlatformEnum = "generic" | "discord" | "slack";

export type InputOfPlatformEnum = "generic" | "discord" | "slack";

export type Policy = {
  public_id: string;
  name: string;
  ast?: unknown;
  preset?: string;
  preset_params?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type InputOfPolicy = {
  name: string;
  ast?: unknown;
  preset?: string;
  preset_params?: Record<string, unknown>;
};

export type PolicyBinding = {
  public_id: string;
  action: ActionEnum;
  policy: string;
  created_at: string;
};

export type InputOfPolicyBinding = {
  action: InputOfActionEnum;
  policy: string;
};

export type PolicyDebugInput = {
  action: ActionEnum;
  subject_type?: SubjectTypeEnum;
  subject_id?: string;
};

export type InputOfPolicyDebugInput = {
  action: InputOfActionEnum;
  subject_type?: InputOfSubjectTypeEnum;
  subject_id?: string;
};

export type PolicyDebugResponse = {
  action: ActionEnum;
  subject_type: string | null;
  subject_id: string | null;
  checked_at: string;
  facts: unknown;
  policy: unknown;
  policy_allowed: boolean | null;
  allowed: boolean;
  reason: string;
  exception_grant_reason: string | null;
  error: string | null;
  trace: unknown;
};

export type InputOfPolicyDebugResponse = {
  action: InputOfActionEnum;
  subject_type: string | null;
  subject_id: string | null;
  checked_at: string;
  facts: unknown;
  policy: unknown;
  policy_allowed: boolean | null;
  allowed: boolean;
  reason: string;
  exception_grant_reason: string | null;
  error: string | null;
  trace: unknown;
};

export type PoolMembership = {
  public_id: string;
  judge: string;
  track_expertise: string[];
  created_at: string;
};

export type InputOfPoolMembership = {};

export type PoolMembershipInputSchema = {
  judge: string;
  track_expertise?: string[];
};

export type InputOfPoolMembershipInputSchema = {
  judge: string;
  track_expertise?: string[];
};

export type PoolStrategyEnum = "all_judges" | "assigned_subset";

export type InputOfPoolStrategyEnum = "all_judges" | "assigned_subset";

export type PreflightCheckSchema = {
  code: string;
  severity: string;
  detail: string;
};

export type InputOfPreflightCheckSchema = {
  code: string;
  severity: string;
  detail: string;
};

export type PreflightSchema = {
  status: string;
  checks: PreflightCheckSchema[];
};

export type InputOfPreflightSchema = {
  status: string;
  checks: InputOfPreflightCheckSchema[];
};

export type PrivacyApplyInput = { apply?: boolean };

export type InputOfPrivacyApplyInput = { apply?: boolean };

export type PrivacyReportOutput = {
  applied: boolean;
  erased: Record<string, unknown>;
  retained?: Record<string, unknown>;
  retained_reason?: string;
  due?: Record<string, unknown>;
};

export type InputOfPrivacyReportOutput = {
  applied: boolean;
  erased: Record<string, unknown>;
  retained?: Record<string, unknown>;
  retained_reason?: string;
  due?: Record<string, unknown>;
};

export type Project = {
  public_id: string;
  name: string;
  description?: string;
  team: string | null;
  track: string | null;
  created_at: string;
  updated_at: string;
  members: ProjectMembership[];
};

export type InputOfProject = { name: string; description?: string };

export type ProjectCOIAttribute = {
  public_id: string;
  project: string;
  kind: COIRelationshipKind;
  value: string;
  created_at: string;
};

export type InputOfProjectCOIAttribute = {
  kind: InputOfCOIRelationshipKind;
  value: string;
};

export type ProjectCOIAttributeInputSchema = {
  project: string;
  kind: ProjectCOIAttributeKind;
  value: string;
};

export type InputOfProjectCOIAttributeInputSchema = {
  project: string;
  kind: InputOfProjectCOIAttributeKind;
  value: string;
};

export type ProjectCOIAttributeKind = "institution" | "domain";

export type InputOfProjectCOIAttributeKind = "institution" | "domain";

export type ProjectCreateInputSchema = {
  name: string;
  description?: string;
  team?: string | null;
  track?: string | null;
};

export type InputOfProjectCreateInputSchema = {
  name: string;
  description?: string;
  team?: string | null;
  track?: string | null;
};

export type ProjectMembership = {
  user: string;
  role: ProjectMembershipRoleEnum;
  joined_at: string;
};

export type InputOfProjectMembership = {
  role: InputOfProjectMembershipRoleEnum;
};

export type ProjectMembershipRoleEnum = "owner" | "contributor";

export type InputOfProjectMembershipRoleEnum = "owner" | "contributor";

export type ProjectRecordInput = { project: string };

export type InputOfProjectRecordInput = { project: string };

export type ProvenanceAwardSchema = {
  award: string;
  name: string;
  winner: string;
  rank_at_selection: number | null;
  override_reason: string;
  published: boolean;
};

export type InputOfProvenanceAwardSchema = {
  award: string;
  name: string;
  winner: string;
  rank_at_selection: number | null;
  override_reason: string;
  published: boolean;
};

export type ProvenanceBallotSchema = {
  ballot: string;
  judge: string;
  rubric_version: string;
  responses: ProvenanceCriterionSchema[];
  weighted_score: number;
  judge_effect: number;
  adjusted_score: number;
  submitted_at: string;
};

export type InputOfProvenanceBallotSchema = {
  ballot: string;
  judge: string;
  rubric_version: string;
  responses: InputOfProvenanceCriterionSchema[];
  weighted_score: number;
  judge_effect: number;
  adjusted_score: number;
  submitted_at: string;
};

export type ProvenanceCriterionSchema = {
  criterion_id: string;
  criterion_name: string;
  weight: number;
  score: number;
};

export type InputOfProvenanceCriterionSchema = {
  criterion_id: string;
  criterion_name: string;
  weight: number;
  score: number;
};

export type ProvenanceSchema = {
  project: string;
  project_name: string;
  rank: number;
  raw_score: number | null;
  final_score: number;
  tie_break: number | null;
  normalization_run: string;
  ridge_lambda: number;
  converged: boolean;
  grand_mean: number;
  ballot_snapshot_available: boolean;
  ballots: ProvenanceBallotSchema[] | null;
  awards: ProvenanceAwardSchema[];
};

export type InputOfProvenanceSchema = {
  project: string;
  project_name: string;
  rank: number;
  raw_score: number | null;
  final_score: number;
  tie_break: number | null;
  normalization_run: string;
  ridge_lambda: number;
  converged: boolean;
  grand_mean: number;
  ballot_snapshot_available: boolean;
  ballots: InputOfProvenanceBallotSchema[] | null;
  awards: InputOfProvenanceAwardSchema[];
};

export type PublicAnnouncementOutput = {
  public_id: string;
  title: string;
  body: string;
  created_at: string;
};

export type InputOfPublicAnnouncementOutput = {};

export type PublicAwardOutput = {
  public_id: string;
  name: string;
  description: string;
  eligibility_track: string | null;
  require_finalized_submission: boolean;
  selection_source: string;
  evaluation_plan: string | null;
  winner_count: number;
  allow_stacking: boolean;
  conflict_group: string;
  published_at: string | null;
  components: ComponentOutput[];
  winners: PublicWinnerOutput[];
};

export type InputOfPublicAwardOutput = {
  public_id: string;
  name: string;
  description: string;
  eligibility_track: string | null;
  require_finalized_submission: boolean;
  selection_source: string;
  evaluation_plan: string | null;
  winner_count: number;
  allow_stacking: boolean;
  conflict_group: string;
  published_at: string | null;
  components: InputOfComponentOutput[];
  winners: InputOfPublicWinnerOutput[];
};

export type PublicEventSchema = {
  public_id: string;
  name: string;
  slug: string;
  description: string;
  timezone: string;
  starts_at: string | null;
  ends_at: string | null;
  status: string;
  tracks: Track[];
  base_prizes: BasePrize[];
};

export type InputOfPublicEventSchema = {
  public_id: string;
  name: string;
  slug: string;
  description: string;
  timezone: string;
  starts_at: string | null;
  ends_at: string | null;
  status: string;
  tracks: InputOfTrack[];
  base_prizes: InputOfBasePrize[];
};

export type PublicWinnerOutput = { project: string; project_name: string };

export type InputOfPublicWinnerOutput = {
  project: string;
  project_name: string;
};

export type PublicationInput = {
  opens_at: string;
  closes_at?: string | null;
  finalist_stage?: string | null;
};

export type InputOfPublicationInput = {
  opens_at: string;
  closes_at?: string | null;
  finalist_stage?: string | null;
};

export type PublicationOutput = {
  surface: SurfaceEnum;
  opens_at: string;
  closes_at: string | null;
  finalist_stage: string | null;
  updated_at: string;
};

export type InputOfPublicationOutput = {
  opens_at: string;
  closes_at: string | null;
  finalist_stage: string | null;
};

export type PublicationRequestInput = {
  plan: string;
  normalization_run: string;
  tie_breaks?: Record<string, number>;
  reason?: string;
};

export type InputOfPublicationRequestInput = {
  plan: string;
  normalization_run: string;
  tie_breaks?: Record<string, number>;
  reason?: string;
};

export type QualifierEntryInput = {
  external_ref: string;
  project?: string | null;
};

export type InputOfQualifierEntryInput = {
  external_ref: string;
  project?: string | null;
};

export type QualifierEntryOutput = {
  external_ref: string;
  project: string;
  advanced: boolean;
};

export type InputOfQualifierEntryOutput = {
  external_ref: string;
  project: string;
  advanced: boolean;
};

export type QualifierImportInput = { entries: QualifierEntryInput[] };

export type InputOfQualifierImportInput = {
  entries: InputOfQualifierEntryInput[];
};

export type QualifierImportOutput = {
  public_id: string;
  stage: string;
  entries: QualifierEntryOutput[];
  advanced_count: number;
  created_at: string;
};

export type InputOfQualifierImportOutput = {
  public_id: string;
  stage: string;
  entries: InputOfQualifierEntryOutput[];
  advanced_count: number;
  created_at: string;
};

export type QuestionInput = { question: string };

export type InputOfQuestionInput = { question: string };

export type QuestionOutput = {
  public_id: string;
  question: string;
  answer: string;
  status: EventQuestionStatus;
  version: number;
  created_at: string;
  updated_at: string;
};

export type InputOfQuestionOutput = {};

export type QuestionReviewInput = {
  version: number;
  status: EventQuestionStatus;
  answer?: string;
  note: string;
};

export type InputOfQuestionReviewInput = {
  version: number;
  status: InputOfEventQuestionStatus;
  answer?: string;
  note: string;
};

export type RankedResultSchema = {
  rank: number;
  project: string | null;
  project_name: string | null;
  raw_score: number | null;
  final_score: number;
  tie_break: number | null;
};

export type InputOfRankedResultSchema = {
  rank: number;
  project: string | null;
  project_name: string | null;
  raw_score: number | null;
  final_score: number;
  tie_break: number | null;
};

export type RecordOutput = { token: string; claims: Record<string, unknown> };

export type InputOfRecordOutput = {
  token: string;
  claims: Record<string, unknown>;
};

export type RedeemInviteInput = { token: string };

export type InputOfRedeemInviteInput = { token: string };

export type RegistrationInviteCode = {
  public_id: string;
  code: string;
  max_uses?: number;
  use_count: number;
  created_at: string;
  revoked_at: string | null;
};

export type InputOfRegistrationInviteCode = { max_uses?: number };

export type RegistrationSettings = {
  mode?: RegistrationSettingsModeEnum;
  capacity?: number | null;
  waitlist_enabled?: boolean;
  updated_at: string;
};

export type InputOfRegistrationSettings = {
  mode?: InputOfRegistrationSettingsModeEnum;
  capacity?: number | null;
  waitlist_enabled?: boolean;
};

export type RegistrationSettingsModeEnum =
  "open" | "application" | "invite_only";

export type InputOfRegistrationSettingsModeEnum =
  "open" | "application" | "invite_only";

export type ReminderInputSchema = {
  kind: ReminderInputSchemaKindEnum;
  due_at: string;
  audience_kind: string;
  audience_params?: Record<string, string>;
  subject: string;
  body: string;
};

export type InputOfReminderInputSchema = {
  kind: InputOfReminderInputSchemaKindEnum;
  due_at: string;
  audience_kind: string;
  audience_params?: Record<string, string>;
  subject: string;
  body: string;
};

export type ReminderInputSchemaKindEnum = "deadline" | "judging" | "voting";

export type InputOfReminderInputSchemaKindEnum =
  "deadline" | "judging" | "voting";

export type ReminderSchema = {
  public_id: string;
  kind: string;
  due_at: string;
  audience_kind: string;
  audience_params: unknown;
  subject: string;
  body: string;
  status: string;
  sent_message: string | null;
  cancelled_at: string | null;
  last_error: string;
};

export type InputOfReminderSchema = {
  public_id: string;
  kind: string;
  due_at: string;
  audience_kind: string;
  audience_params: unknown;
  subject: string;
  body: string;
  status: string;
  sent_message: string | null;
  cancelled_at: string | null;
  last_error: string;
};

export type ResolutionInputSchema = { resolution_note: string };

export type InputOfResolutionInputSchema = { resolution_note: string };

export type ResourceInput = {
  kind: ResourceInputKindEnum;
  title: string;
  url?: string;
  body?: string;
  position?: number;
};

export type InputOfResourceInput = {
  kind: InputOfResourceInputKindEnum;
  title: string;
  url?: string;
  body?: string;
  position?: number;
};

export type ResourceInputKindEnum =
  "api" | "starter_repo" | "contact" | "faq" | "workshop" | "other";

export type InputOfResourceInputKindEnum =
  "api" | "starter_repo" | "contact" | "faq" | "workshop" | "other";

export type ResourceOutput = {
  public_id: string;
  kind: string;
  title: string;
  url: string;
  body: string;
  position: number;
};

export type InputOfResourceOutput = {
  public_id: string;
  kind: string;
  title: string;
  url: string;
  body: string;
  position: number;
};

export type RespondInput = { response: string };

export type InputOfRespondInput = { response: string };

export type ResultsPublishInputSchema = {
  normalization_run: string;
  tie_breaks?: Record<string, number>;
  reason?: string;
};

export type InputOfResultsPublishInputSchema = {
  normalization_run: string;
  tie_breaks?: Record<string, number>;
  reason?: string;
};

export type RetentionPolicyInput = {
  participant_data_days: number | null;
  private_artifact_days: number | null;
};

export type InputOfRetentionPolicyInput = {
  participant_data_days: number | null;
  private_artifact_days: number | null;
};

export type RetentionPolicyOutput = {
  participant_data_days: number | null;
  private_artifact_days: number | null;
  updated_at: string | null;
};

export type InputOfRetentionPolicyOutput = {
  participant_data_days: number | null;
  private_artifact_days: number | null;
  updated_at: string | null;
};

export type ReviewOutput = {
  project: string;
  status: string;
  decision_note: string;
  revision: number;
  decided_at: string | null;
  findings: FindingOutput[];
};

export type InputOfReviewOutput = {
  project: string;
  status: string;
  decision_note: string;
  revision: number;
  decided_at: string | null;
  findings: InputOfFindingOutput[];
};

export type ReviewSummaryOutput = {
  project: string;
  project_name: string;
  status: string;
  open_findings: number;
  addressed_findings: number;
  revision: number;
};

export type InputOfReviewSummaryOutput = {
  project: string;
  project_name: string;
  status: string;
  open_findings: number;
  addressed_findings: number;
  revision: number;
};

export type RoomOutput = {
  public_id: string;
  status: string;
  quorum: number;
  notes: Record<string, unknown>[];
  stances: Record<string, unknown>[];
  tally: Record<string, unknown>[];
  finalization: Record<string, unknown>;
};

export type InputOfRoomOutput = {
  public_id: string;
  status: string;
  quorum: number;
  notes: Record<string, unknown>[];
  stances: Record<string, unknown>[];
  tally: Record<string, unknown>[];
  finalization: Record<string, unknown>;
};

export type RubricLabCriterionSchema = {
  criterion_id: string;
  name: string;
  weight_share: number;
  response_count: number;
  missing_count: number;
  mean: number | null;
  variance: number | null;
  scale_use: number | null;
  at_min_count: number;
  at_max_count: number;
  spread_share: number | null;
  dominates: boolean;
  weight_scenarios: RubricLabScenarioSchema[];
};

export type InputOfRubricLabCriterionSchema = {
  criterion_id: string;
  name: string;
  weight_share: number;
  response_count: number;
  missing_count: number;
  mean: number | null;
  variance: number | null;
  scale_use: number | null;
  at_min_count: number;
  at_max_count: number;
  spread_share: number | null;
  dominates: boolean;
  weight_scenarios: InputOfRubricLabScenarioSchema[];
};

export type RubricLabInputSchema = {
  rubric_version?: string;
  factors?: number[];
};

export type InputOfRubricLabInputSchema = {
  rubric_version?: string;
  factors?: number[];
};

export type RubricLabScenarioSchema = {
  factor: number;
  order: string[];
  rank_changed_count: number;
  top_changed: boolean;
};

export type InputOfRubricLabScenarioSchema = {
  factor: number;
  order: string[];
  rank_changed_count: number;
  top_changed: boolean;
};

export type RubricLabSchema = {
  rubric_version: string;
  ballot_count: number;
  baseline: string[];
  criteria: RubricLabCriterionSchema[];
};

export type InputOfRubricLabSchema = {
  rubric_version: string;
  ballot_count: number;
  baseline: string[];
  criteria: InputOfRubricLabCriterionSchema[];
};

export type RubricVersion = {
  public_id: string;
  number: number;
  criteria: unknown;
  published_at: string;
};

export type InputOfRubricVersion = { number: number; criteria: unknown };

export type RulesAcknowledgeInput = { number?: number };

export type InputOfRulesAcknowledgeInput = { number?: number };

export type RulesInput = {
  min_team_size: number | null;
  max_team_size: number | null;
  required_artifact_kinds: string[];
  require_finalized_submission: boolean;
  require_track: boolean;
  require_clearance: boolean;
};

export type InputOfRulesInput = {
  min_team_size: number | null;
  max_team_size: number | null;
  required_artifact_kinds: string[];
  require_finalized_submission: boolean;
  require_track: boolean;
  require_clearance: boolean;
};

export type RulesOutput = {
  min_team_size: number | null;
  max_team_size: number | null;
  required_artifact_kinds: string[];
  require_finalized_submission: boolean;
  require_track: boolean;
  require_clearance: boolean;
  updated_at: string | null;
};

export type InputOfRulesOutput = {
  min_team_size: number | null;
  max_team_size: number | null;
  required_artifact_kinds: string[];
  require_finalized_submission: boolean;
  require_track: boolean;
  require_clearance: boolean;
  updated_at: string | null;
};

export type SavedSearchInput = { name: string; filters: SearchFilters };

export type InputOfSavedSearchInput = {
  name: string;
  filters: InputOfSearchFilters;
};

export type SavedSearchOutput = {
  public_id: string;
  name: string;
  filters: unknown;
  created_at: string;
};

export type InputOfSavedSearchOutput = {};

export type ScanInput = { token: string };

export type InputOfScanInput = { token: string };

export type SearchFilters = {
  q?: string;
  tags?: string[];
  artifact_kind?: ArtifactKindEnum;
  track?: string;
  stage?: string;
};

export type InputOfSearchFilters = {
  q?: string;
  tags?: string[];
  artifact_kind?: InputOfArtifactKindEnum;
  track?: string;
  stage?: string;
};

export type SearchItemOutput = {
  public_id: string;
  name: string;
  description: string;
  track: string | null;
  team: string | null;
  url: string;
  tags: string[];
  artifact_kinds: string[];
};

export type InputOfSearchItemOutput = {
  public_id: string;
  name: string;
  description: string;
  track: string | null;
  team: string | null;
  url: string;
  tags: string[];
  artifact_kinds: string[];
};

export type SearchOutput = {
  count: number;
  next_offset: number | null;
  items: SearchItemOutput[];
};

export type InputOfSearchOutput = {
  count: number;
  next_offset: number | null;
  items: InputOfSearchItemOutput[];
};

export type SelectionSourceEnum = "manual" | "evaluation" | "community";

export type InputOfSelectionSourceEnum = "manual" | "evaluation" | "community";

export type SensitivityInputSchema = {
  ridge_lambdas?: number[];
  holdout_counts?: number[];
};

export type InputOfSensitivityInputSchema = {
  ridge_lambdas?: number[];
  holdout_counts?: number[];
};

export type SettingsInput = { require_publication_approval: boolean };

export type InputOfSettingsInput = { require_publication_approval: boolean };

export type SeverityEnum = "blocking" | "advisory";

export type InputOfSeverityEnum = "blocking" | "advisory";

export type SignedArchiveImportInput = {
  name: string;
  slug: string;
  envelope: unknown;
};

export type InputOfSignedArchiveImportInput = {
  name: string;
  slug: string;
  envelope: unknown;
};

export type SignedArchiveOutput = {
  manifest: Record<string, unknown>;
  archive: Record<string, unknown>;
  public_key_pem: string;
  signature: string;
};

export type InputOfSignedArchiveOutput = {
  manifest: Record<string, unknown>;
  archive: Record<string, unknown>;
  public_key_pem: string;
  signature: string;
};

export type SponsorProjectSchema = {
  public_id: string;
  name: string;
  team_name: string | null;
  track_name: string | null;
};

export type InputOfSponsorProjectSchema = {
  public_id: string;
  name: string;
  team_name: string | null;
  track_name: string | null;
};

export type Stage = {
  public_id: string;
  name: string;
  position?: number;
  is_initial?: boolean;
  participation_mode?: ParticipationModeEnum;
  created_at: string;
};

export type InputOfStage = {
  name: string;
  position?: number;
  is_initial?: boolean;
  participation_mode?: InputOfParticipationModeEnum;
};

export type StageTransition = {
  public_id: string;
  from_stage: string;
  to_stage: string;
  created_at: string;
};

export type InputOfStageTransition = { from_stage: string; to_stage: string };

export type StanceEnum = "endorse" | "object" | "abstain";

export type InputOfStanceEnum = "endorse" | "object" | "abstain";

export type StanceInput = { stance: StanceEnum; rationale?: string };

export type InputOfStanceInput = {
  stance: InputOfStanceEnum;
  rationale?: string;
};

export type SubjectExportOutput = {
  subject: Record<string, unknown>;
  event: string;
  data: Record<string, unknown>;
  retained_data: Record<string, unknown>;
  artifacts: Record<string, unknown>[];
};

export type InputOfSubjectExportOutput = {
  subject: Record<string, unknown>;
  event: string;
  data: Record<string, unknown>;
  retained_data: Record<string, unknown>;
  artifacts: Record<string, unknown>[];
};

export type SubjectInput = { type: TaxonomySubjectType; id?: string };

export type InputOfSubjectInput = {
  type: InputOfTaxonomySubjectType;
  id?: string;
};

export type SubjectKindEnum = "role" | "user";

export type InputOfSubjectKindEnum = "role" | "user";

export type SubjectTypeEnum = "project" | "team";

export type InputOfSubjectTypeEnum = "project" | "team";

export type SubmissionDiffSchema = {
  from_version: number;
  to_version: number;
  diff: unknown;
};

export type InputOfSubmissionDiffSchema = {
  from_version: number;
  to_version: number;
  diff: unknown;
};

export type SubmissionDraftInputSchema = {
  draft_payload: unknown;
  draft_revision: number;
};

export type InputOfSubmissionDraftInputSchema = {
  draft_payload: unknown;
  draft_revision: number;
};

export type SubmissionFinalizeInputSchema = { draft_revision: number };

export type InputOfSubmissionFinalizeInputSchema = { draft_revision: number };

export type SubmissionPreviewArtifactSchema = {
  id: string;
  title: string;
  kind: string;
  drift: string | null;
  inspection: unknown;
  download_url: string | null;
};

export type InputOfSubmissionPreviewArtifactSchema = {
  id: string;
  title: string;
  kind: string;
  drift: string | null;
  inspection: unknown;
  download_url: string | null;
};

export type SubmissionPreviewSchema = {
  version: number;
  verified: boolean;
  artifacts: SubmissionPreviewArtifactSchema[];
};

export type InputOfSubmissionPreviewSchema = {
  version: number;
  verified: boolean;
  artifacts: InputOfSubmissionPreviewArtifactSchema[];
};

export type SubmissionReceiptSchema = {
  submission: SubmissionSchema;
  receipt: string;
};

export type InputOfSubmissionReceiptSchema = {
  submission: InputOfSubmissionSchema;
  receipt: string;
};

export type SubmissionReopenInputSchema = { reason?: string };

export type InputOfSubmissionReopenInputSchema = { reason?: string };

export type SubmissionSchema = {
  public_id: string;
  stage: string;
  status: string;
  draft_payload: unknown;
  draft_revision: number;
  current_version: string | null;
  versions: SubmissionVersionSchema[];
};

export type InputOfSubmissionSchema = {
  public_id: string;
  stage: string;
  status: string;
  draft_payload: unknown;
  draft_revision: number;
  current_version: string | null;
  versions: InputOfSubmissionVersionSchema[];
};

export type SubmissionStageSchema = {
  public_id: string;
  name: string;
  submission: SubmissionSchema | null;
};

export type InputOfSubmissionStageSchema = {
  public_id: string;
  name: string;
  submission: InputOfSubmissionSchema | null;
};

export type SubmissionVersionSchema = {
  public_id: string;
  number: number;
  digest: string;
  finalized_at: string;
  finalized_by: string;
};

export type InputOfSubmissionVersionSchema = {
  public_id: string;
  number: number;
  digest: string;
  finalized_at: string;
  finalized_by: string;
};

export type SubscriptionInput = {
  url: string;
  event_types: string[];
  event?: string | null;
  platform?: PlatformEnum;
};

export type InputOfSubscriptionInput = {
  url: string;
  event_types: string[];
  event?: string | null;
  platform?: InputOfPlatformEnum;
};

export type SubscriptionIssued = {
  public_id: string;
  url: string;
  event_types: string[];
  event: string | null;
  platform: string;
  enabled: boolean;
  created_at: string;
  secret: string;
};

export type InputOfSubscriptionIssued = {
  public_id: string;
  url: string;
  event_types: string[];
  event: string | null;
  platform: string;
  enabled: boolean;
  created_at: string;
  secret: string;
};

export type SubscriptionOutput = {
  public_id: string;
  url: string;
  event_types: string[];
  event: string | null;
  platform: string;
  enabled: boolean;
  created_at: string;
};

export type InputOfSubscriptionOutput = {
  public_id: string;
  url: string;
  event_types: string[];
  event: string | null;
  platform: string;
  enabled: boolean;
  created_at: string;
};

export type SurfaceEnum =
  "gallery" | "finalists" | "feedback" | "winners" | "archive";

export type InputOfSurfaceEnum =
  "gallery" | "finalists" | "feedback" | "winners" | "archive";

export type TagInput = { tags: string[] };

export type InputOfTagInput = { tags: string[] };

export type TaxonomyCreateInput = {
  key: string;
  name: string;
  applies_to: TaxonomySubjectType;
  allows_multiple?: boolean;
  terms?: TermInput[];
};

export type InputOfTaxonomyCreateInput = {
  key: string;
  name: string;
  applies_to: InputOfTaxonomySubjectType;
  allows_multiple?: boolean;
  terms?: InputOfTermInput[];
};

export type TaxonomyOutput = {
  public_id: string;
  key: string;
  name: string;
  applies_to: string;
  allows_multiple: boolean;
  terms: TermOutput[];
};

export type InputOfTaxonomyOutput = {
  public_id: string;
  key: string;
  name: string;
  applies_to: string;
  allows_multiple: boolean;
  terms: InputOfTermOutput[];
};

export type TaxonomySubjectType = "project" | "person" | "event";

export type InputOfTaxonomySubjectType = "project" | "person" | "event";

export type Team = {
  public_id: string;
  name: string;
  created_at: string;
  members: TeamMembership[];
};

export type InputOfTeam = { name: string };

export type TeamInvite = {
  public_id: string;
  token: string;
  created_at: string;
  expires_at: string | null;
  max_uses: number;
  use_count: number;
  revoked_at: string | null;
};

export type InputOfTeamInvite = {};

export type TeamMembership = {
  user_public_id: string;
  username: string;
  role?: TeamMembershipRoleEnum;
  joined_at: string;
};

export type InputOfTeamMembership = { role?: InputOfTeamMembershipRoleEnum };

export type TeamMembershipRoleEnum = "member" | "captain";

export type InputOfTeamMembershipRoleEnum = "member" | "captain";

export type TeamOpeningInput = {
  title: string;
  description?: string;
  desired_skills: string[];
  desired_roles?: string[];
  interests?: string[];
  min_availability_hours_per_week?: number | null;
  project?: string | null;
  is_open?: boolean;
};

export type InputOfTeamOpeningInput = {
  title: string;
  description?: string;
  desired_skills: string[];
  desired_roles?: string[];
  interests?: string[];
  min_availability_hours_per_week?: number | null;
  project?: string | null;
  is_open?: boolean;
};

export type TeamOpeningSchema = {
  public_id: string;
  team: string;
  team_name: string;
  project: string | null;
  project_name: string | null;
  title: string;
  description: string;
  desired_skills: string[];
  desired_roles: string[];
  interests: string[];
  min_availability_hours_per_week: number | null;
  is_open: boolean;
  matched_skills: string[];
  matched_roles?: string[];
  matched_interests?: string[];
  availability_compatible?: boolean | null;
};

export type InputOfTeamOpeningSchema = {
  public_id: string;
  team: string;
  team_name: string;
  project: string | null;
  project_name: string | null;
  title: string;
  description: string;
  desired_skills: string[];
  desired_roles: string[];
  interests: string[];
  min_availability_hours_per_week: number | null;
  is_open: boolean;
  matched_skills: string[];
  matched_roles?: string[];
  matched_interests?: string[];
  availability_compatible?: boolean | null;
};

export type TemporalGate = {
  public_id: string;
  name: string;
  opens_at?: string | null;
  closes_at?: string | null;
  event_local_opens_at: string | null;
  event_local_closes_at: string | null;
  dst_warning: string | null;
  created_at: string;
};

export type InputOfTemporalGate = {
  name: string;
  opens_at?: string | null;
  closes_at?: string | null;
};

export type TermInput = { key: string; label: string };

export type InputOfTermInput = { key: string; label: string };

export type TermOutput = { key: string; label: string; position: number };

export type InputOfTermOutput = {
  key: string;
  label: string;
  position: number;
};

export type ThemeEnum = "default" | "dark" | "minimal";

export type InputOfThemeEnum = "default" | "dark" | "minimal";

export type TimelineWindowSchema = {
  label: string;
  opens_at: string | null;
  closes_at: string | null;
  event_local_opens_at: string | null;
  event_local_closes_at: string | null;
  dst_warning: string | null;
};

export type InputOfTimelineWindowSchema = {
  label: string;
  opens_at: string | null;
  closes_at: string | null;
  event_local_opens_at: string | null;
  event_local_closes_at: string | null;
  dst_warning: string | null;
};

export type Track = {
  public_id: string;
  name: string;
  description?: string;
  position?: number;
};

export type InputOfTrack = {
  name: string;
  description?: string;
  position?: number;
};

export type TransferCaptainInput = { user: string };

export type InputOfTransferCaptainInput = { user: string };

export type UploadCompleteInputSchema = { parts?: unknown };

export type InputOfUploadCompleteInputSchema = { parts?: unknown };

export type UploadIntentInputSchema = {
  kind: string;
  visibility: string;
  title?: string;
  byte_size: number;
  content_type: string;
};

export type InputOfUploadIntentInputSchema = {
  kind: string;
  visibility: string;
  title?: string;
  byte_size: number;
  content_type: string;
};

export type UploadIntentSchema = {
  artifact: ArtifactSchema;
  intent: string;
  expires_at: string;
  upload: unknown;
};

export type InputOfUploadIntentSchema = {
  artifact: InputOfArtifactSchema;
  intent: string;
  expires_at: string;
  upload: unknown;
};

export type UserSummarySchema = {
  public_id: string;
  username: string;
  memberships: MembershipSummarySchema[];
};

export type InputOfUserSummarySchema = {
  public_id: string;
  username: string;
  memberships: InputOfMembershipSummarySchema[];
};

export type ValidationSchema = { outcome: string; detail: string };

export type InputOfValidationSchema = { outcome: string; detail: string };

export type VerificationKeyOutput = {
  issuer: string;
  algorithm: string;
  public_key_pem: string;
};

export type InputOfVerificationKeyOutput = {
  issuer: string;
  algorithm: string;
  public_key_pem: string;
};

export type VerifyRecordInput = { token: string };

export type InputOfVerifyRecordInput = { token: string };

export type VerifyRecordOutput = {
  valid: boolean;
  claims?: Record<string, unknown>;
  error?: string;
};

export type InputOfVerifyRecordOutput = {
  valid: boolean;
  claims?: Record<string, unknown>;
  error?: string;
};

export type VoteInputSchema = { project: string; token?: string };

export type InputOfVoteInputSchema = { project: string; token?: string };

export type VoteReceiptSchema = { public_id: string };

export type InputOfVoteReceiptSchema = { public_id: string };

export type VoteToken = {
  public_id: string;
  token?: string;
  redeemed_at?: string | null;
  created_at: string;
};

export type InputOfVoteToken = { token?: string; redeemed_at?: string | null };

export type VoteTokenBatchInputSchema = { count?: number };

export type InputOfVoteTokenBatchInputSchema = { count?: number };

export type VotingPlan = {
  public_id: string;
  identity_mode?: IdentityModeEnum;
  opens_at: string;
  closes_at: string;
  allow_comments?: boolean;
  comment_visibility?: CommentVisibilityEnum;
  results_published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InputOfVotingPlan = {
  identity_mode?: InputOfIdentityModeEnum;
  opens_at: string;
  closes_at: string;
  allow_comments?: boolean;
  comment_visibility?: InputOfCommentVisibilityEnum;
};

export type VotingResultSchema = {
  project: string;
  name: string;
  votes: number;
};

export type InputOfVotingResultSchema = {
  project: string;
  name: string;
  votes: number;
};

export type VotingStatusSchema = {
  identity_mode: string;
  opens_at: string;
  closes_at: string;
  is_open: boolean;
  allow_comments: boolean;
};

export type InputOfVotingStatusSchema = {
  identity_mode: string;
  opens_at: string;
  closes_at: string;
  is_open: boolean;
  allow_comments: boolean;
};

export type WinnerInput = { project: string; override_reason?: string };

export type InputOfWinnerInput = { project: string; override_reason?: string };

export type WinnerOutput = {
  public_id: string;
  project: string;
  project_name: string;
  source: string;
  evidence: unknown;
  override_reason: string;
  selected_at: string;
  fulfillments: Record<string, unknown>[];
};

export type InputOfWinnerOutput = {
  public_id: string;
  project: string;
  project_name: string;
  source: string;
  evidence: unknown;
  override_reason: string;
  selected_at: string;
  fulfillments: Record<string, unknown>[];
};

export type WorkflowPresetInput = { preset: string };

export type InputOfWorkflowPresetInput = { preset: string };

export type WorkflowPresetResult = { stages: Stage[]; plans: EvaluationPlan[] };

export type InputOfWorkflowPresetResult = {
  stages: InputOfStage[];
  plans: InputOfEvaluationPlan[];
};

export type WorkspaceInputSchema = { name: string; slug?: string };

export type InputOfWorkspaceInputSchema = { name: string; slug?: string };

export type WorkspaceSchema = { public_id: string; name: string; slug: string };

export type InputOfWorkspaceSchema = {
  public_id: string;
  name: string;
  slug: string;
};

export interface Operations {
  post_api_v1_accounts_login: {
    request: { body: InputOfLoginInputSchema };
    response: LoginResponseSchema;
  };
  post_api_v1_accounts_logout: { request: {}; response: null };
  get_api_v1_accounts_me: { request: {}; response: UserSummarySchema };
  get_api_v1_accounts_oidc_callback: {
    request: { query?: { code?: string; error?: string; state?: string } };
    response: never;
  };
  get_api_v1_accounts_oidc_config: { request: {}; response: OidcConfigSchema };
  get_api_v1_accounts_oidc_login: {
    request: { query?: { next?: string } };
    response: never;
  };
  get_api_v1_audit_workspace_public_id: {
    request: { path: { workspace_public_id: string } };
    response: AuditEventSchema[];
  };
  get_api_v1_audit_workspace_public_id_events_event_public_id_config_history: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ConfigHistoryEntrySchema[];
  };
  post_api_v1_audit_workspace_public_id_events_event_public_id_config_history_audit_event_public_id_restore: {
    request: {
      path: {
        audit_event_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ConfigRestoreResultSchema;
  };
  get_api_v1_events_event_public_id: {
    request: { path: { event_public_id: string } };
    response: PublicEventSchema;
  };
  get_api_v1_events_event_public_id_announcements: {
    request: { path: { event_public_id: string }; query?: { offset?: number } };
    response: PublicAnnouncementOutput[];
  };
  get_api_v1_events_event_public_id_awards: {
    request: { path: { event_public_id: string } };
    response: PublicAwardOutput[];
  };
  get_api_v1_events_event_public_id_finalists: {
    request: { path: { event_public_id: string } };
    response: GalleryItemOutput[];
  };
  get_api_v1_events_event_public_id_gallery: {
    request: { path: { event_public_id: string } };
    response: GalleryItemOutput[];
  };
  get_api_v1_events_event_public_id_questions: {
    request: { path: { event_public_id: string }; query?: { offset?: number } };
    response: QuestionOutput[];
  };
  get_api_v1_events_event_public_id_result_corrections: {
    request: { path: { event_public_id: string } };
    response: Record<string, unknown>[];
  };
  get_api_v1_events_event_public_id_search: {
    request: {
      path: { event_public_id: string };
      query?: {
        artifact_kind?:
          | "dataset"
          | "document"
          | "external_video"
          | "file"
          | "image"
          | "live_url"
          | "repository"
          | "secret"
          | "video";
        offset?: number;
        q?: string;
        stage?: string;
        tags?: string[];
        track?: string;
      };
    };
    response: SearchOutput;
  };
  get_api_v1_export_csv: { request: {}; response: string };
  get_api_v1_gallery: { request: {}; response: GalleryProjectSchema[] };
  get_api_v1_health: { request: {}; response: HealthResponse };
  get_api_v1_judge_scores: { request: {}; response: JudgeScoreSchema[] };
  get_api_v1_public_events_event_public_id_voting_candidates: {
    request: { path: { event_public_id: string } };
    response: CandidateSchema[];
  };
  post_api_v1_public_events_event_public_id_voting_request_email_token: {
    request: {
      path: { event_public_id: string };
      body: InputOfEmailTokenInputSchema;
    };
    response: EmailTokenReceiptSchema;
  };
  get_api_v1_public_events_event_public_id_voting_results: {
    request: { path: { event_public_id: string } };
    response: VotingResultSchema[];
  };
  get_api_v1_public_events_event_public_id_voting_status: {
    request: { path: { event_public_id: string } };
    response: VotingStatusSchema;
  };
  post_api_v1_public_events_event_public_id_voting_votes: {
    request: {
      path: { event_public_id: string };
      body: InputOfVoteInputSchema;
    };
    response: VoteReceiptSchema;
  };
  get_api_v1_records_verification_key: {
    request: {};
    response: VerificationKeyOutput;
  };
  post_api_v1_records_verify: {
    request: { body: InputOfVerifyRecordInput };
    response: VerifyRecordOutput;
  };
  get_api_v1_schema: {
    request: { query?: { format?: "json" | "yaml"; lang?: "en" | "es" } };
    response: Record<string, unknown>;
  };
  post_api_v1_submit: { request: {}; response: never };
  post_api_v1_workspaces: {
    request: { body: InputOfWorkspaceInputSchema };
    response: WorkspaceSchema;
  };
  get_api_v1_workspaces_workspace_public_id_api_credentials: {
    request: { path: { workspace_public_id: string } };
    response: CredentialReadSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_api_credentials: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfCredentialCreateSchema;
    };
    response: CredentialIssuedSchema;
  };
  post_api_v1_workspaces_workspace_public_id_api_credentials_credential_public_id_revoke: {
    request: {
      path: { credential_public_id: string; workspace_public_id: string };
    };
    response: CredentialReadSchema;
  };
  post_api_v1_workspaces_workspace_public_id_archive_import: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfArchiveImportInput;
    };
    response: ImportedEventOutput;
  };
  post_api_v1_workspaces_workspace_public_id_archive_preview: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfArchiveImportInput;
    };
    response: ArchivePreviewOutput;
  };
  post_api_v1_workspaces_workspace_public_id_archive_signed_import: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfSignedArchiveImportInput;
    };
    response: ImportedEventOutput;
  };
  get_api_v1_workspaces_workspace_public_id_event_templates: {
    request: { path: { workspace_public_id: string } };
    response: EventTemplateOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_event_templates: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfEventTemplateCreateInput;
    };
    response: EventTemplateOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_event_templates_template_public_id: {
    request: {
      path: { template_public_id: string; workspace_public_id: string };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_event_templates_template_public_id_instantiate: {
    request: {
      path: { template_public_id: string; workspace_public_id: string };
      body: InputOfInstantiateInput;
    };
    response: ImportedEventOutput;
  };
  get_api_v1_workspaces_workspace_public_id_event_templates_library: {
    request: { path: { workspace_public_id: string } };
    response: LibraryTemplateOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_event_templates_library_template_slug_instantiate: {
    request: {
      path: { template_slug: string; workspace_public_id: string };
      body: InputOfInstantiateInput;
    };
    response: ImportedEventOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events: {
    request: { path: { workspace_public_id: string } };
    response: Event;
  };
  post_api_v1_workspaces_workspace_public_id_events: {
    request: { path: { workspace_public_id: string }; body: InputOfEvent };
    response: Event;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Event;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfPatchedEvent;
    };
    response: Event;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_accessibility_conformance: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ConformanceReportOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Announcement;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfAnnouncement;
    };
    response: Announcement;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements_announcement_public_id: {
    request: {
      path: {
        announcement_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_applications: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: EventApplication[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_applications_application_public_id_decide: {
    request: {
      path: {
        application_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfApplicationDecisionInputSchema;
    };
    response: EventApplication;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: { mode?: "config" | "final" | "full" };
    };
    response: ArchiveOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive_signed: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: { mode?: "config" | "final" | "full" };
    };
    response: SignedArchiveOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code_apply: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfEventAsCodeApplyInput;
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code_plan: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfEventAsCodeDocumentInput;
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code_validate: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfEventAsCodeDocumentInput;
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_attendance: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_authz_dry_run: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfAuthzDryRunInputSchema;
    };
    response: AuthzDryRunOutputSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: AwardOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfAwardInput;
    };
    response: AwardOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_components: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfComponentInput;
    };
    response: ComponentOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: RoomOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfOpenInput;
    };
    response: RoomOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_close: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: RoomOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_finalize: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfFinalizeInput;
    };
    response: RoomOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_notes: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfNoteInput;
    };
    response: RoomOutput;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_projects_project_public_id_stance: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfStanceInput;
    };
    response: RoomOutput;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_fulfillments_fulfillment_public_id: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        fulfillment_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedFulfillmentInput;
    };
    response: FulfillmentOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_publish: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: AwardOutput;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_sponsors_user_public_id: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        user_public_id: string;
        workspace_public_id: string;
      };
    };
    response: AwardOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_sponsors_user_public_id: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        user_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_winners: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfWinnerInput;
    };
    response: WinnerOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_candidates: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: CandidateOutput[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_fulfillment_export: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: {
        include_notes?: boolean;
        include_recipients?: boolean;
        state?:
          "claimed" | "contacted" | "failed" | "pending" | "sent" | "verified";
      };
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_fulfillment_export_csv: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: {
        include_notes?: boolean;
        include_recipients?: boolean;
        state?:
          "claimed" | "contacted" | "failed" | "pending" | "sent" | "verified";
      };
    };
    response: string;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_proposals: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: AwardProposalOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: BasePrize;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfBasePrize;
    };
    response: BasePrize;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes_prize_public_id: {
    request: {
      path: {
        event_public_id: string;
        prize_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedBasePrize;
    };
    response: BasePrize;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes_prize_public_id: {
    request: {
      path: {
        event_public_id: string;
        prize_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_challenges: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ChallengeOutput[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_check_ins: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: CheckIn[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_check_ins: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfCheckInInputSchema;
    };
    response: CheckIn;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_checkins_scan: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfScanInput;
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_clone: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfCloneInput;
    };
    response: ImportedEventOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ProjectCOIAttribute[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfProjectCOIAttributeInputSchema;
    };
    response: ProjectCOIAttribute;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes_attribute_public_id: {
    request: {
      path: {
        attribute_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: JudgeCOIRelationship[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfJudgeCOIRelationshipInputSchema;
    };
    response: JudgeCOIRelationship;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships_relationship_public_id: {
    request: {
      path: {
        event_public_id: string;
        relationship_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_rules: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: COIRuleOutputSchema[];
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_rules: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfCOIRuleInputSchema;
    };
    response: COIRuleOutputSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_announcements_source_public_id_review: {
    request: {
      path: {
        event_public_id: string;
        source_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfAnnouncementReviewInput;
    };
    response: AnnouncementReviewOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_audiences: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: AudienceKindSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_audiences_preview: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfAudiencePreviewInputSchema;
    };
    response: AudiencePreviewSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_messages: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: MessageSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_messages: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfMessageInputSchema;
    };
    response: MessageSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: { offset?: number };
    };
    response: QuestionOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfQuestionInput;
    };
    response: QuestionOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions_source_public_id_review: {
    request: {
      path: {
        event_public_id: string;
        source_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfQuestionReviewInput;
    };
    response: QuestionOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ReminderSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfReminderInputSchema;
    };
    response: ReminderSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders_reminder_public_id_cancel: {
    request: {
      path: {
        event_public_id: string;
        reminder_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ReminderSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_dashboard: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: EventDashboardSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_reviews: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: {
        status?: "cleared" | "ineligible" | "needs_remediation" | "pending";
      };
    };
    response: ReviewSummaryOutput[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_rules: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: RulesOutput;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_rules: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfRulesInput;
    };
    response: RulesOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: EvaluationPool;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfEvaluationPool;
    };
    response: EvaluationPool;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships: {
    request: {
      path: {
        event_public_id: string;
        pool_public_id: string;
        workspace_public_id: string;
      };
    };
    response: PoolMembership;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships: {
    request: {
      path: {
        event_public_id: string;
        pool_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfPoolMembershipInputSchema;
    };
    response: PoolMembership;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships_membership_public_id: {
    request: {
      path: {
        event_public_id: string;
        membership_public_id: string;
        pool_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_suggest_judges: {
    request: {
      path: {
        event_public_id: string;
        pool_public_id: string;
        workspace_public_id: string;
      };
    };
    response: JudgeSuggestionSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_grants: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ExceptionGrant;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_grants: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfExceptionGrant;
    };
    response: ExceptionGrant;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests_request_public_id_approve: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfExceptionApprovalInput;
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests_request_public_id_cancel: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfExceptionApprovalInput;
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests_request_public_id_reject: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfExceptionApprovalInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: FormPayloadSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfFormNameInputSchema;
    };
    response: FormPayloadSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id: {
    request: {
      path: {
        event_public_id: string;
        form_public_id: string;
        workspace_public_id: string;
      };
    };
    response: FormPayloadSchema;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id: {
    request: {
      path: {
        event_public_id: string;
        form_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfFormDraftInputSchema;
    };
    response: FormPayloadSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_publish: {
    request: {
      path: {
        event_public_id: string;
        form_public_id: string;
        workspace_public_id: string;
      };
    };
    response: FormVersionSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_versions: {
    request: {
      path: {
        event_public_id: string;
        form_public_id: string;
        workspace_public_id: string;
      };
    };
    response: FormVersionSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_versions_version_public_id_restore: {
    request: {
      path: {
        event_public_id: string;
        form_public_id: string;
        version_public_id: string;
        workspace_public_id: string;
      };
    };
    response: FormPayloadSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_governance_settings: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_governance_settings: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfSettingsInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_calendar: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: JudgeCalendarSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_conflicts: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ConflictOfInterest;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_conflicts: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfConflictOfInterest;
    };
    response: ConflictOfInterest;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: JudgeInvitationSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfJudgeInvitationInputSchema;
    };
    response: JudgeInvitationSchema;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations_invitation_public_id: {
    request: {
      path: {
        event_public_id: string;
        invitation_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_workload: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: JudgeWorkloadRowSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_locations: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: LocationOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_locations: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfLocationInput;
    };
    response: LocationOutput;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_location_public_id: {
    request: {
      path: {
        event_public_id: string;
        location_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedLocationPatchInput;
    };
    response: LocationOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_location_public_id: {
    request: {
      path: {
        event_public_id: string;
        location_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_auto_assign: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfApplyInput;
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_matches: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: TeamOpeningSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_my_openings: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: TeamOpeningSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: TeamOpeningSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfTeamOpeningInput;
    };
    response: TeamOpeningSchema;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings_opening_public_id: {
    request: {
      path: {
        event_public_id: string;
        opening_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedTeamOpeningInput;
    };
    response: TeamOpeningSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings_opening_public_id_matches: {
    request: {
      path: {
        event_public_id: string;
        opening_public_id: string;
        workspace_public_id: string;
      };
    };
    response: MarketplaceProfileSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profile: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: MyMarketplaceProfileResponse;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profile: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfMarketplaceProfileInput;
    };
    response: MarketplaceProfileSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profiles: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: MarketplaceProfileSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_cancel: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_claim: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_reassign: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_resolve: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_queue: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_mentors: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_mentors_me: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_application: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: MyEventApplicationResponse;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_application: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfApplyToEventInputSchema;
    };
    response: EventApplication;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_attendance: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, unknown>;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_my_attendance: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfAttendanceInput;
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_pass: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_pass_qr: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: string;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: MyTeamResponse;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfCreateTeamInput;
    };
    response: Team;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: TeamInvite;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfCreateTeamInviteInput;
    };
    response: TeamInvite;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites_invite_public_id: {
    request: {
      path: {
        event_public_id: string;
        invite_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_leave: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_transfer_captain: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfTransferCaptainInput;
    };
    response: Team;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours_slot_public_id_signups: {
    request: {
      path: {
        event_public_id: string;
        slot_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours_signups_signup_public_id: {
    request: {
      path: {
        event_public_id: string;
        signup_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_onsite_summary: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_analytics: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: { plan_offset?: number };
    };
    response: EventAnalyticsResponse;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_bulk: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfBulkRequest;
    };
    response: BulkResponse;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_checklist: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: LaunchChecklistSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: {
        kind?: "artifact" | "content" | "duplicate" | "eligibility" | "voting";
        offset?: number;
      };
    };
    response: ModerationQueueResponse;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation_reviews: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: {
        kind?: "artifact" | "content" | "duplicate" | "eligibility" | "voting";
        offset?: number;
      };
    };
    response: ModerationReviewResponse[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation_reviews: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfModerationReviewInput;
    };
    response: ModerationReviewResponse;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_summary: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: OperationsSummarySchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_page: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Page;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_page: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfPatchedPage;
    };
    response: Page;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_page_accessibility_audit: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: AccessibilityWarning[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: PageBlock;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfPageBlock;
    };
    response: PageBlock;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_block_public_id: {
    request: {
      path: {
        block_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedPageBlock;
    };
    response: PageBlock;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_block_public_id: {
    request: {
      path: {
        block_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_reorder: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfPageBlockOrderInput;
    };
    response: PageBlock[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_permission_matrix: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: PermissionMatrixEntrySchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_policies: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Policy;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_policies: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfPolicy;
    };
    response: Policy;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_policies_policy_public_id: {
    request: {
      path: {
        event_public_id: string;
        policy_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedPolicy;
    };
    response: Policy;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_policies_policy_public_id: {
    request: {
      path: {
        event_public_id: string;
        policy_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: PolicyBinding;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfPolicyBinding;
    };
    response: PolicyBinding;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings_binding_public_id: {
    request: {
      path: {
        binding_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_debug: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfPolicyDebugInput;
    };
    response: PolicyDebugResponse;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_presets: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, { label: string; params: string[] }>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_policy: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: RetentionPolicyOutput;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_policy: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfRetentionPolicyInput;
    };
    response: RetentionPolicyOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_run: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfPrivacyApplyInput;
    };
    response: PrivacyReportOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_subjects_user_public_id_erase: {
    request: {
      path: {
        event_public_id: string;
        user_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPrivacyApplyInput;
    };
    response: PrivacyReportOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_subjects_user_public_id_export: {
    request: {
      path: {
        event_public_id: string;
        user_public_id: string;
        workspace_public_id: string;
      };
    };
    response: SubjectExportOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_project_locations: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Project;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfProjectCreateInputSchema;
    };
    response: Project;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Project;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedProjectPatchInputSchema;
    };
    response: Project;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ArtifactSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfExternalArtifactInputSchema;
    };
    response: ArtifactSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ArtifactSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_check_evidence: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ArtifactSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_inspection: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_inspection: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_upload_intents_intent_public_id_complete: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        intent_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfUploadCompleteInputSchema;
    };
    response: ArtifactSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_validate: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ArtifactSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_preflight: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: PreflightSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_upload_intents: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfUploadIntentInputSchema;
    };
    response: UploadIntentSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Comment;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfComment;
    };
    response: Comment;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments_comment_public_id_hide: {
    request: {
      path: {
        comment_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Comment;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ReviewOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_checks: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ReviewOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_decision: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfDecisionInput;
    };
    response: ReviewOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfFindingInput;
    };
    response: FindingOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings_finding_public_id_close: {
    request: {
      path: {
        event_public_id: string;
        finding_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfCloseInput;
    };
    response: FindingOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings_finding_public_id_respond: {
    request: {
      path: {
        event_public_id: string;
        finding_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfRespondInput;
    };
    response: FindingOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_exception_requests: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_exception_requests: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfExceptionRequestInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ParticipantFormSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms_version_public_id_response: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        version_public_id: string;
        workspace_public_id: string;
      };
    };
    response: FormResponseSchema;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms_version_public_id_response: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        version_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfFormAnswersInputSchema;
    };
    response: FormResponseSchema;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_location: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfPlacementInput;
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_members: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfAddProjectMemberInput;
    };
    response: ProjectMembership;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_notes: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: MentorNote[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_notes: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfMentorNoteInputSchema;
    };
    response: MentorNote;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_requests: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_requests: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_review_artifacts: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_review_artifacts_artifact_public_id_inspection: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_review_artifacts_artifact_public_id_inspection: {
    request: {
      path: {
        artifact_public_id: string;
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: SubmissionStageSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: SubmissionSchema;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfSubmissionDraftInputSchema;
    };
    response: SubmissionSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_diff: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: SubmissionDiffSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_finalize: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfSubmissionFinalizeInputSchema;
    };
    response: SubmissionReceiptSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_preview: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: SubmissionPreviewSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_receipt: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_reopen: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfSubmissionReopenInputSchema;
    };
    response: SubmissionSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_tags: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
    };
    response: TagInput;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_tags: {
    request: {
      path: {
        event_public_id: string;
        project_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfTagInput;
    };
    response: TagInput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: PublicationOutput[];
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules_surface: {
    request: {
      path: {
        event_public_id: string;
        surface: string;
        workspace_public_id: string;
      };
      query?: {
        surface?: "archive" | "feedback" | "finalists" | "gallery" | "winners";
      };
      body: InputOfPublicationInput;
    };
    response: PublicationOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules_surface: {
    request: {
      path: {
        event_public_id: string;
        surface: string;
        workspace_public_id: string;
      };
      query?: {
        surface?: "archive" | "feedback" | "finalists" | "gallery" | "winners";
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_event: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: RecordOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_judge: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfJudgeRecordInput;
    };
    response: RecordOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_project: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfProjectRecordInput;
    };
    response: RecordOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: RegistrationInviteCode[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfRegistrationInviteCode;
    };
    response: RegistrationInviteCode;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes_code_public_id: {
    request: {
      path: {
        code_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_settings: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: RegistrationSettings;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_settings: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfRegistrationSettings;
    };
    response: RegistrationSettings;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_result_corrections: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfPublicationRequestInput;
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests_request_public_id_approve: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfDecisionNoteInput;
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests_request_public_id_cancel: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfDecisionNoteInput;
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests_request_public_id_reject: {
    request: {
      path: {
        event_public_id: string;
        request_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfDecisionNoteInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_rules: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_rules: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfParticipantRulesInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_rules_number: {
    request: {
      path: {
        event_public_id: string;
        number: number;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_rules_acknowledge: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfRulesAcknowledgeInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_rules_acknowledgements: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: SavedSearchOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfSavedSearchInput;
    };
    response: SavedSearchOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches_view_public_id: {
    request: {
      path: {
        event_public_id: string;
        view_public_id: string;
        workspace_public_id: string;
      };
      query?: { offset?: number };
    };
    response: SearchOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches_view_public_id: {
    request: {
      path: {
        event_public_id: string;
        view_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards_award_public_id_resources: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfResourceInput;
    };
    response: ResourceOutput;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards_award_public_id_resources_resource_public_id: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        resource_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedResourceInput;
    };
    response: ResourceOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards_award_public_id_resources_resource_public_id: {
    request: {
      path: {
        award_public_id: string;
        event_public_id: string;
        resource_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_fulfillments_fulfillment_public_id: {
    request: {
      path: {
        event_public_id: string;
        fulfillment_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedFulfillmentInput;
    };
    response: FulfillmentOutput;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_projects: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: SponsorProjectSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_evidence: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: AdvancementEvidenceSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_graph_validate: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: GraphValidationSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: StageTransition;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfStageTransition;
    };
    response: StageTransition;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions_transition_public_id: {
    request: {
      path: {
        event_public_id: string;
        transition_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Stage;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfStage;
    };
    response: Stage;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedStage;
    };
    response: Stage;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_advance: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: AdvancementStrategiesSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_advance: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfAdvancementInputSchema;
    };
    response: AdvancementResultSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: EvaluationPlan;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfEvaluationPlan;
    };
    response: EvaluationPlan;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: EvaluationPlan;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedEvaluationPlan;
    };
    response: EvaluationPlan;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_agreement: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: AgreementSummarySchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: AppealSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfAppealInputSchema;
    };
    response: AppealSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals_appeal_public_id_decide: {
    request: {
      path: {
        appeal_public_id: string;
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfAppealDecisionInputSchema;
    };
    response: AppealSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignment_responses: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: AssignmentVersion;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_activate: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfAssignmentActivateInputSchema;
    };
    response: AssignmentVersion;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_activate_optimized: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfAssignmentActivateInputSchema;
    };
    response: AssignmentVersion;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_compare: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfAssignmentCompareInputSchema;
    };
    response: AssignmentCompareSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_dropout_simulation: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfDropoutSimulationInputSchema;
    };
    response: DropoutSimulationSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_preview: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfAssignmentPreviewInputSchema;
    };
    response: AssignmentCoveragePreviewSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_rebalance: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfAssignmentRebalanceInputSchema;
    };
    response: AssignmentVersion;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_audit_capsule: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Ballot;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfBallotSubmitInputSchema;
    };
    response: Ballot;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: BallotDraft;
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfBallotDraftInputSchema;
    };
    response: BallotDraft;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_projects: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: CalibrationProjectItemSchema[];
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_projects: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfCalibrationProjectsInputSchema;
    };
    response: CalibrationProjectItemSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_ballots: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Ballot;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_ballots: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfBallotSubmitInputSchema;
    };
    response: Ballot;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_status: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: CalibrationStatusSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_summary: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: CalibrationProjectSummarySchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_candidates: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: CandidateQueueItemSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_close_calls: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: CloseCallsSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_explain_project_public_id: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_feedback_project_public_id: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: FeedbackEntrySchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_assignments: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_assignments_project_public_id_respond: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfAssignmentResponseInput;
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_route: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      query?: { remaining_only?: boolean; start?: string };
    };
    response: Record<string, unknown>;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_normalization_runs: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: NormalizationRun;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_normalization_runs: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfNormalizationInputSchema;
    };
    response: NormalizationRun;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_comparisons: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: PairwiseComparison;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_comparisons: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfPairwiseComparisonInputSchema;
    };
    response: PairwiseComparison;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_next: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: PairwiseNextPairSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_publish_results: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfPairwiseResultsPublishInputSchema;
    };
    response: EvaluationPlan;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_results: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: PairwiseRankedResultSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_results_csv: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: string;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_runs: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: PairwiseRun;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_runs: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPairwiseRunInputSchema;
    };
    response: PairwiseRun;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_progress: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: EvaluationProgressSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_provenance_project_public_id: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        project_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: ProvenanceSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_results: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfResultsPublishInputSchema;
    };
    response: EvaluationPlan;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_rubric: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: RubricVersion;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_rubric: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: RubricVersion;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_results: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: RankedResultSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_results_csv: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: string;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_routes: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      query?: { remaining_only?: boolean; start?: string };
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_rubric_lab: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfRubricLabInputSchema;
    };
    response: RubricLabSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_rubric_versions_rubric_version_public_id_restore: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        rubric_version_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: EvaluationPlan;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_runs_run_public_id_replay: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        run_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      query?: { timeline?: boolean };
    };
    response: Record<string, unknown>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_sensitivity: {
    request: {
      path: {
        event_public_id: string;
        plan_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfSensitivityInputSchema;
    };
    response: {
      ridge_lambda?: {
        baseline?: string[];
        scenarios?: Record<
          string,
          { order?: string[]; rank_changed?: boolean }
        >;
      };
      judge_removal?: {
        baseline?: string[];
        scenarios?: Record<
          string,
          { order?: string[]; rank_changed?: boolean }
        >;
      };
      incompleteness?: {
        baseline?: string[];
        scenarios?: Record<
          string,
          { order?: string[]; rank_changed?: boolean }
        >;
      };
    };
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_external_qualifiers: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
    };
    response: QualifierImportOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_external_qualifiers: {
    request: {
      path: {
        event_public_id: string;
        stage_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfQualifierImportInput;
    };
    response: QualifierImportOutput;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_status: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfEventStatusInput;
    };
    response: Event;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_taxonomy_assignments: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      query?: {
        subject_type?: "event" | "person" | "project";
        taxonomy?: string;
        term?: string;
      };
    };
    response: AssignmentOutput[];
  };
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_taxonomy_assignments: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfAssignmentInput;
    };
    response: AssignmentOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_team_invites_redeem: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfRedeemInviteInput;
    };
    response: Team;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: TemporalGate;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfTemporalGate;
    };
    response: TemporalGate;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates_gate_public_id: {
    request: {
      path: {
        event_public_id: string;
        gate_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedTemporalGate;
    };
    response: TemporalGate;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_timezone_timeline: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: TimelineWindowSchema[];
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_timezone_timeline: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Track;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfTrack;
    };
    response: Track;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks_track_public_id: {
    request: {
      path: {
        event_public_id: string;
        track_public_id: string;
        workspace_public_id: string;
      };
      body?: InputOfPatchedTrack;
    };
    response: Track;
  };
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks_track_public_id: {
    request: {
      path: {
        event_public_id: string;
        track_public_id: string;
        workspace_public_id: string;
      };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: VotingPlan;
  };
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfPatchedVotingPlan;
    };
    response: VotingPlan;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_abuse_signals: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: AbuseSignalSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_abuse_signals_signal_public_id_resolve: {
    request: {
      path: {
        event_public_id: string;
        signal_public_id: string;
        workspace_public_id: string;
      };
      body: InputOfResolutionInputSchema;
    };
    response: AbuseSignalSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_audit: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: CommunityAuditSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_publish_results: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: VotingPlan;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_tokens: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: VoteToken;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_tokens: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body?: InputOfVoteTokenBatchInputSchema;
    };
    response: VoteToken[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_candidates: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: CandidateSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_request_email_token: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfEmailTokenInputSchema;
    };
    response: EmailTokenReceiptSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_results: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: VotingResultSchema[];
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_status: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: VotingStatusSchema;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_votes: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfVoteInputSchema;
    };
    response: VoteReceiptSchema;
  };
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_workflow_presets: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: Record<string, { label: string; rounds: string[] }>;
  };
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_workflow_presets_apply: {
    request: {
      path: { event_public_id: string; workspace_public_id: string };
      body: InputOfWorkflowPresetInput;
    };
    response: WorkflowPresetResult;
  };
  get_api_v1_workspaces_workspace_public_id_inbox: {
    request: { path: { workspace_public_id: string } };
    response: InboxMessageSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_inbox_recipient_public_id_read: {
    request: {
      path: { recipient_public_id: string; workspace_public_id: string };
    };
    response: InboxMessageSchema;
  };
  get_api_v1_workspaces_workspace_public_id_judge_directory: {
    request: { path: { workspace_public_id: string } };
    response: JudgeDirectorySchema[];
  };
  get_api_v1_workspaces_workspace_public_id_judge_events: {
    request: { path: { workspace_public_id: string } };
    response: JudgeEventSummary[];
  };
  get_api_v1_workspaces_workspace_public_id_judge_expertise_judge_public_id: {
    request: { path: { judge_public_id: string; workspace_public_id: string } };
    response: ExpertiseOutputSchema;
  };
  put_api_v1_workspaces_workspace_public_id_judge_expertise_judge_public_id: {
    request: {
      path: { judge_public_id: string; workspace_public_id: string };
      body: InputOfExpertiseInputSchema;
    };
    response: ExpertiseOutputSchema;
  };
  get_api_v1_workspaces_workspace_public_id_members: {
    request: { path: { workspace_public_id: string } };
    response: MembershipSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_members: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfMembershipInputSchema;
    };
    response: MembershipSchema;
  };
  get_api_v1_workspaces_workspace_public_id_my_judge_expertise: {
    request: { path: { workspace_public_id: string } };
    response: ExpertiseOutputSchema;
  };
  put_api_v1_workspaces_workspace_public_id_my_judge_expertise: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfExpertiseInputSchema;
    };
    response: ExpertiseOutputSchema;
  };
  get_api_v1_workspaces_workspace_public_id_my_judge_invitations: {
    request: { path: { workspace_public_id: string } };
    response: JudgeInvitationSchema[];
  };
  post_api_v1_workspaces_workspace_public_id_my_judge_invitations_invitation_public_id_respond: {
    request: {
      path: { invitation_public_id: string; workspace_public_id: string };
      body: InputOfJudgeInvitationDecisionSchema;
    };
    response: JudgeInvitationSchema;
  };
  get_api_v1_workspaces_workspace_public_id_operator_console: {
    request: { path: { workspace_public_id: string } };
    response: OperatorConsoleSchema;
  };
  get_api_v1_workspaces_workspace_public_id_participant_events: {
    request: { path: { workspace_public_id: string } };
    response: ParticipantEventSummary[];
  };
  get_api_v1_workspaces_workspace_public_id_taxonomies: {
    request: { path: { workspace_public_id: string } };
    response: TaxonomyOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_taxonomies: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfTaxonomyCreateInput;
    };
    response: TaxonomyOutput;
  };
  get_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id: {
    request: {
      path: { taxonomy_public_id: string; workspace_public_id: string };
    };
    response: TaxonomyOutput;
  };
  patch_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id: {
    request: {
      path: { taxonomy_public_id: string; workspace_public_id: string };
      body?: InputOfPatchedTaxonomyPatchInput;
    };
    response: TaxonomyOutput;
  };
  delete_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id: {
    request: {
      path: { taxonomy_public_id: string; workspace_public_id: string };
    };
    response: null;
  };
  get_api_v1_workspaces_workspace_public_id_webhooks: {
    request: { path: { workspace_public_id: string } };
    response: SubscriptionOutput[];
  };
  post_api_v1_workspaces_workspace_public_id_webhooks: {
    request: {
      path: { workspace_public_id: string };
      body: InputOfSubscriptionInput;
    };
    response: SubscriptionIssued;
  };
  patch_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id: {
    request: {
      path: { subscription_public_id: string; workspace_public_id: string };
      body?: InputOfPatchedSubscriptionUpdate;
    };
    response: SubscriptionOutput;
  };
  get_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries: {
    request: {
      path: { subscription_public_id: string; workspace_public_id: string };
    };
    response: DeliveryOutput[];
  };
  get_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries_delivery_public_id: {
    request: {
      path: {
        delivery_public_id: string;
        subscription_public_id: string;
        workspace_public_id: string;
      };
    };
    response: DeliveryInspection;
  };
  post_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries_delivery_public_id_replay: {
    request: {
      path: {
        delivery_public_id: string;
        subscription_public_id: string;
        workspace_public_id: string;
      };
    };
    response: DeliveryOutput;
  };
}

export const operations = {
  post_api_v1_accounts_login: {
    method: "POST",
    path: "/api/v1/accounts/login/",
    path_params: [],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_accounts_logout: {
    method: "POST",
    path: "/api/v1/accounts/logout/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  get_api_v1_accounts_me: {
    method: "GET",
    path: "/api/v1/accounts/me/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_accounts_oidc_callback: {
    method: "GET",
    path: "/api/v1/accounts/oidc/callback/",
    path_params: [],
    query_params: ["code", "error", "state"],
    request_body: false,
    response_kind: "none",
  },
  get_api_v1_accounts_oidc_config: {
    method: "GET",
    path: "/api/v1/accounts/oidc/config/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_accounts_oidc_login: {
    method: "GET",
    path: "/api/v1/accounts/oidc/login/",
    path_params: [],
    query_params: ["next"],
    request_body: false,
    response_kind: "none",
  },
  get_api_v1_audit_workspace_public_id: {
    method: "GET",
    path: "/api/v1/audit/{workspace_public_id}/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_audit_workspace_public_id_events_event_public_id_config_history: {
    method: "GET",
    path: "/api/v1/audit/{workspace_public_id}/events/{event_public_id}/config-history/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_audit_workspace_public_id_events_event_public_id_config_history_audit_event_public_id_restore:
    {
      method: "POST",
      path: "/api/v1/audit/{workspace_public_id}/events/{event_public_id}/config-history/{audit_event_public_id}/restore/",
      path_params: [
        "audit_event_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_events_event_public_id: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_announcements: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/announcements/",
    path_params: ["event_public_id"],
    query_params: ["offset"],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_awards: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/awards/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_finalists: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/finalists/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_gallery: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/gallery/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_questions: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/questions/",
    path_params: ["event_public_id"],
    query_params: ["offset"],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_result_corrections: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/result-corrections/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_events_event_public_id_search: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/search/",
    path_params: ["event_public_id"],
    query_params: ["artifact_kind", "offset", "q", "stage", "tags", "track"],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_export_csv: {
    method: "GET",
    path: "/api/v1/export.csv",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "text",
  },
  get_api_v1_gallery: {
    method: "GET",
    path: "/api/v1/gallery/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_health: {
    method: "GET",
    path: "/api/v1/health/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_judge_scores: {
    method: "GET",
    path: "/api/v1/judge/scores/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_public_events_event_public_id_voting_candidates: {
    method: "GET",
    path: "/api/v1/public/events/{event_public_id}/voting/candidates/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_public_events_event_public_id_voting_request_email_token: {
    method: "POST",
    path: "/api/v1/public/events/{event_public_id}/voting/request-email-token/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_public_events_event_public_id_voting_results: {
    method: "GET",
    path: "/api/v1/public/events/{event_public_id}/voting/results/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_public_events_event_public_id_voting_status: {
    method: "GET",
    path: "/api/v1/public/events/{event_public_id}/voting/status/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_public_events_event_public_id_voting_votes: {
    method: "POST",
    path: "/api/v1/public/events/{event_public_id}/voting/votes/",
    path_params: ["event_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_records_verification_key: {
    method: "GET",
    path: "/api/v1/records/verification-key/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_records_verify: {
    method: "POST",
    path: "/api/v1/records/verify/",
    path_params: [],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_schema: {
    method: "GET",
    path: "/api/v1/schema/",
    path_params: [],
    query_params: ["format", "lang"],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_submit: {
    method: "POST",
    path: "/api/v1/submit/",
    path_params: [],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  post_api_v1_workspaces: {
    method: "POST",
    path: "/api/v1/workspaces/",
    path_params: [],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_api_credentials: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/api-credentials/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_api_credentials: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/api-credentials/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_api_credentials_credential_public_id_revoke:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/api-credentials/{credential_public_id}/revoke/",
      path_params: ["credential_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_archive_import: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/archive/import/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_archive_preview: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/archive/preview/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_archive_signed_import: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/archive/signed/import/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_event_templates: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/event-templates/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_event_templates: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/event-templates/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  delete_api_v1_workspaces_workspace_public_id_event_templates_template_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/event-templates/{template_public_id}/",
      path_params: ["template_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_event_templates_template_public_id_instantiate:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/event-templates/{template_public_id}/instantiate/",
      path_params: ["template_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_event_templates_library: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/event-templates/library/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_event_templates_library_template_slug_instantiate:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/event-templates/library/{template_slug}/instantiate/",
      path_params: ["template_slug", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id: {
    method: "PATCH",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id: {
    method: "DELETE",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_accessibility_conformance:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/accessibility-conformance/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/announcements/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/announcements/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_announcements_announcement_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/announcements/{announcement_public_id}/",
      path_params: [
        "announcement_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_applications:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/applications/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_applications_application_public_id_decide:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/applications/{application_public_id}/decide/",
      path_params: [
        "application_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/archive/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: ["mode"],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive_signed:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/archive/signed/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["mode"],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/as-code/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code_apply:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/as-code/apply/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code_plan:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/as-code/plan/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_as_code_validate:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/as-code/validate/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_attendance: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/attendance/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_authz_dry_run:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/authz-dry-run/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_components:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/components/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_close:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/close/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_finalize:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/finalize/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_notes:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/notes/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_deliberation_projects_project_public_id_stance:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/deliberation/projects/{project_public_id}/stance/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_fulfillments_fulfillment_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/fulfillments/{fulfillment_public_id}/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "fulfillment_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_publish:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/publish/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_sponsors_user_public_id:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/sponsors/{user_public_id}/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "user_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_sponsors_user_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/sponsors/{user_public_id}/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "user_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_award_public_id_winners:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/{award_public_id}/winners/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_candidates:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/candidates/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_fulfillment_export:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/fulfillment-export/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["include_notes", "include_recipients", "state"],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_fulfillment_export_csv:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/fulfillment-export.csv",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["include_notes", "include_recipients", "state"],
      request_body: false,
      response_kind: "text",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_awards_proposals:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/awards/proposals/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes_prize_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/{prize_public_id}/",
      path_params: [
        "event_public_id",
        "prize_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_base_prizes_prize_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/base-prizes/{prize_public_id}/",
      path_params: [
        "event_public_id",
        "prize_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_challenges: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/challenges/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_check_ins: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/check-ins/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_check_ins: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/check-ins/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_checkins_scan:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/checkins/scan/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_clone: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/clone/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-project-attributes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-project-attributes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_project_attributes_attribute_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-project-attributes/{attribute_public_id}/",
      path_params: [
        "attribute_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-relationships/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-relationships/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_relationships_relationship_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-relationships/{relationship_public_id}/",
      path_params: [
        "event_public_id",
        "relationship_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_rules: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-rules/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_coi_rules: {
    method: "PUT",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/coi-rules/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_announcements_source_public_id_review:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/announcements/{source_public_id}/review/",
      path_params: [
        "event_public_id",
        "source_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_audiences:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/audiences/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_audiences_preview:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/audiences/preview/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_messages:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/messages/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_messages:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/messages/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/questions/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["offset"],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/questions/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_questions_source_public_id_review:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/questions/{source_public_id}/review/",
      path_params: [
        "event_public_id",
        "source_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/reminders/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/reminders/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_communications_reminders_reminder_public_id_cancel:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/communications/reminders/{reminder_public_id}/cancel/",
      path_params: [
        "event_public_id",
        "reminder_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_dashboard: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/dashboard/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_reviews:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/eligibility-reviews/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["status"],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_rules:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/eligibility-rules/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_eligibility_rules:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/eligibility-rules/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/memberships/",
      path_params: ["event_public_id", "pool_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/memberships/",
      path_params: ["event_public_id", "pool_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_memberships_membership_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/memberships/{membership_public_id}/",
      path_params: [
        "event_public_id",
        "membership_public_id",
        "pool_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_evaluation_pools_pool_public_id_suggest_judges:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/evaluation-pools/{pool_public_id}/suggest-judges/",
      path_params: ["event_public_id", "pool_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_grants:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-grants/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_grants:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-grants/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-requests/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests_request_public_id_approve:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-requests/{request_public_id}/approve/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests_request_public_id_cancel:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-requests/{request_public_id}/cancel/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_exception_requests_request_public_id_reject:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/exception-requests/{request_public_id}/reject/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/",
      path_params: ["event_public_id", "form_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/",
      path_params: ["event_public_id", "form_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_publish:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/publish/",
      path_params: ["event_public_id", "form_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_versions:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/versions/",
      path_params: ["event_public_id", "form_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_forms_form_public_id_versions_version_public_id_restore:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/forms/{form_public_id}/versions/{version_public_id}/restore/",
      path_params: [
        "event_public_id",
        "form_public_id",
        "version_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_governance_settings:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/governance/settings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_governance_settings:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/governance/settings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_calendar:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-calendar/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_conflicts:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-conflicts/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_conflicts:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-conflicts/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-invitations/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-invitations/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_invitations_invitation_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-invitations/{invitation_public_id}/",
      path_params: [
        "event_public_id",
        "invitation_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_workload:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-workload/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_locations: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_locations: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_location_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/{location_public_id}/",
      path_params: [
        "event_public_id",
        "location_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_location_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/{location_public_id}/",
      path_params: [
        "event_public_id",
        "location_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_locations_auto_assign:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/locations/auto-assign/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_matches:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/matches/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_my_openings:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/my-openings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings_opening_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/{opening_public_id}/",
      path_params: [
        "event_public_id",
        "opening_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_openings_opening_public_id_matches:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/openings/{opening_public_id}/matches/",
      path_params: [
        "event_public_id",
        "opening_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profile:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/profile/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profile:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/profile/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_marketplace_profiles:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/marketplace/profiles/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_cancel:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentor-requests/{request_public_id}/cancel/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_claim:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentor-requests/{request_public_id}/claim/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_reassign:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentor-requests/{request_public_id}/reassign/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_request_public_id_resolve:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentor-requests/{request_public_id}/resolve/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_mentor_requests_queue:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentor-requests/queue/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_mentors: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentors/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_mentors_me: {
    method: "PUT",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/mentors/me/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_application:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-application/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_application:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-application/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_attendance:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-attendance/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_my_attendance:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-attendance/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_pass: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-pass/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_pass_qr: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-pass/qr/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "text",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/invites/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/invites/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_invites_invite_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/invites/{invite_public_id}/",
      path_params: [
        "event_public_id",
        "invite_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_leave:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/leave/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_my_team_transfer_captain:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/my-team/transfer-captain/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/office-hours/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/office-hours/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours_slot_public_id_signups:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/office-hours/{slot_public_id}/signups/",
      path_params: ["event_public_id", "slot_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_office_hours_signups_signup_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/office-hours/signups/{signup_public_id}/",
      path_params: [
        "event_public_id",
        "signup_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_onsite_summary:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/onsite-summary/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_analytics:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/analytics/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["plan_offset"],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_bulk:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/bulk/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_checklist:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/checklist/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/moderation/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["kind", "offset"],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation_reviews:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/moderation/reviews/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["kind", "offset"],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_moderation_reviews:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/moderation/reviews/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_summary:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/summary/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_page: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_page: {
    method: "PATCH",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_page_accessibility_audit:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/accessibility-audit/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_block_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/{block_public_id}/",
      path_params: [
        "block_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_block_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/{block_public_id}/",
      path_params: [
        "block_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_page_blocks_reorder:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/page/blocks/reorder/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_permission_matrix:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/permission-matrix/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_policies: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_policies: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_policies_policy_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/{policy_public_id}/",
      path_params: [
        "event_public_id",
        "policy_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_policies_policy_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policies/{policy_public_id}/",
      path_params: [
        "event_public_id",
        "policy_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-bindings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-bindings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_bindings_binding_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-bindings/{binding_public_id}/",
      path_params: [
        "binding_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_debug:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-debug/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_policy_presets:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/policy-presets/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_policy:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/retention-policy/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_policy:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/retention-policy/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_retention_run:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/retention/run/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_subjects_user_public_id_erase:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/subjects/{user_public_id}/erase/",
      path_params: ["event_public_id", "user_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_privacy_subjects_user_public_id_export:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/privacy/subjects/{user_public_id}/export/",
      path_params: ["event_public_id", "user_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_project_locations:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/project-locations/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_check_evidence:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/check-evidence/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_inspection:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/inspection/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_inspection:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/inspection/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_upload_intents_intent_public_id_complete:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/upload-intents/{intent_public_id}/complete/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "intent_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_artifact_public_id_validate:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/{artifact_public_id}/validate/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_preflight:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/preflight/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_artifacts_upload_intents:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/artifacts/upload-intents/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/comments/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/comments/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_comments_comment_public_id_hide:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/comments/{comment_public_id}/hide/",
      path_params: [
        "comment_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_checks:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/checks/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_decision:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/decision/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/findings/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings_finding_public_id_close:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/findings/{finding_public_id}/close/",
      path_params: [
        "event_public_id",
        "finding_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_eligibility_findings_finding_public_id_respond:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/eligibility/findings/{finding_public_id}/respond/",
      path_params: [
        "event_public_id",
        "finding_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_exception_requests:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/exception-requests/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_exception_requests:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/exception-requests/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/forms/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms_version_public_id_response:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/forms/{version_public_id}/response/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "version_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_forms_version_public_id_response:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/forms/{version_public_id}/response/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "version_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_location:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/location/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_members:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/members/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_notes:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/mentor-notes/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_notes:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/mentor-notes/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_requests:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/mentor-requests/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_mentor_requests:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/mentor-requests/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_review_artifacts:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/review-artifacts/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_review_artifacts_artifact_public_id_inspection:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/review-artifacts/{artifact_public_id}/inspection/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_review_artifacts_artifact_public_id_inspection:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/review-artifacts/{artifact_public_id}/inspection/",
      path_params: [
        "artifact_public_id",
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_diff:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/diff/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_finalize:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/finalize/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_preview:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/preview/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_receipt:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/receipt/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_submissions_stage_public_id_reopen:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/submissions/{stage_public_id}/reopen/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_tags:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/tags/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_projects_project_public_id_tags:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/projects/{project_public_id}/tags/",
      path_params: [
        "event_public_id",
        "project_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/publication-schedules/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules_surface:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/publication-schedules/{surface}/",
      path_params: ["event_public_id", "surface", "workspace_public_id"],
      query_params: ["surface"],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_publication_schedules_surface:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/publication-schedules/{surface}/",
      path_params: ["event_public_id", "surface", "workspace_public_id"],
      query_params: ["surface"],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_event:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/records/event/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_judge:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/records/judge/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_records_project:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/records/project/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-invite-codes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-invite-codes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_invite_codes_code_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-invite-codes/{code_public_id}/",
      path_params: ["code_public_id", "event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_settings:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-settings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_registration_settings:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/registration-settings/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_result_corrections:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/result-corrections/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/result-publication-requests/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/result-publication-requests/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests_request_public_id_approve:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/result-publication-requests/{request_public_id}/approve/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests_request_public_id_cancel:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/result-publication-requests/{request_public_id}/cancel/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_result_publication_requests_request_public_id_reject:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/result-publication-requests/{request_public_id}/reject/",
      path_params: [
        "event_public_id",
        "request_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_rules: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/rules/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_rules: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/rules/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "none",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_rules_number:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/rules/{number}/",
      path_params: ["event_public_id", "number", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_rules_acknowledge:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/rules/acknowledge/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_rules_acknowledgements:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/rules/acknowledgements/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches_view_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/{view_public_id}/",
      path_params: ["event_public_id", "view_public_id", "workspace_public_id"],
      query_params: ["offset"],
      request_body: false,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_saved_searches_view_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/saved-searches/{view_public_id}/",
      path_params: ["event_public_id", "view_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/awards/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards_award_public_id_resources:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/awards/{award_public_id}/resources/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards_award_public_id_resources_resource_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/awards/{award_public_id}/resources/{resource_public_id}/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "resource_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_awards_award_public_id_resources_resource_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/awards/{award_public_id}/resources/{resource_public_id}/",
      path_params: [
        "award_public_id",
        "event_public_id",
        "resource_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_portal_fulfillments_fulfillment_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-portal/fulfillments/{fulfillment_public_id}/",
      path_params: [
        "event_public_id",
        "fulfillment_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_sponsor_projects:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/sponsor-projects/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_evidence:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-evidence/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_graph_validate:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-graph/validate/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-transitions/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-transitions/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stage_transitions_transition_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stage-transitions/{transition_public_id}/",
      path_params: [
        "event_public_id",
        "transition_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_advance:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/advance/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_advance:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/advance/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_agreement:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/agreement/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/appeals/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/appeals/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_appeals_appeal_public_id_decide:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/appeals/{appeal_public_id}/decide/",
      path_params: [
        "appeal_public_id",
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignment_responses:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignment-responses/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_activate:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/activate/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_activate_optimized:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/activate-optimized/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_compare:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/compare/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_dropout_simulation:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/dropout-simulation/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_preview:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/preview/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_assignments_rebalance:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/assignments/rebalance/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_audit_capsule:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/audit-capsule/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/{project_public_id}/draft/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/{project_public_id}/draft/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_ballots_project_public_id_draft:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/ballots/{project_public_id}/draft/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_projects:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration-projects/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_projects:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration-projects/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_ballots:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/ballots/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_ballots:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/ballots/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_status:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/status/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_calibration_summary:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/calibration/summary/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_candidates:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/candidates/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_close_calls:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/close-calls/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_explain_project_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/explain/{project_public_id}/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_feedback_project_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/feedback/{project_public_id}/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_assignments:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/my-assignments/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_assignments_project_public_id_respond:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/my-assignments/{project_public_id}/respond/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_my_route:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/my-route/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: ["remaining_only", "start"],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_normalization_runs:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/normalization-runs/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_normalization_runs:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/normalization-runs/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_comparisons:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/comparisons/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_comparisons:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/comparisons/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_next:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/next/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_publish_results:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/publish-results/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_results:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/results/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_results_csv:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/results.csv",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "text",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_runs:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/runs/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_pairwise_runs:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/pairwise/runs/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_progress:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/progress/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_provenance_project_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/provenance/{project_public_id}/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "project_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_results:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/publish-results/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_rubric:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/publish-rubric/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_publish_rubric:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/publish-rubric/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_results:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/results/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_results_csv:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/results.csv",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "text",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_routes:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/routes/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: ["remaining_only", "start"],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_rubric_lab:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/rubric-lab/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_rubric_versions_rubric_version_public_id_restore:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/rubric-versions/{rubric_version_public_id}/restore/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "rubric_version_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_runs_run_public_id_replay:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/runs/{run_public_id}/replay/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "run_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: ["timeline"],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_evaluation_plans_plan_public_id_sensitivity:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/evaluation-plans/{plan_public_id}/sensitivity/",
      path_params: [
        "event_public_id",
        "plan_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_external_qualifiers:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/external-qualifiers/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_stages_stage_public_id_external_qualifiers:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/stages/{stage_public_id}/external-qualifiers/",
      path_params: [
        "event_public_id",
        "stage_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_status: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/status/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_taxonomy_assignments:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/taxonomy-assignments/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: ["subject_type", "taxonomy", "term"],
      request_body: false,
      response_kind: "json",
    },
  put_api_v1_workspaces_workspace_public_id_events_event_public_id_taxonomy_assignments:
    {
      method: "PUT",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/taxonomy-assignments/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_team_invites_redeem:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/team-invites/redeem/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates_gate_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/{gate_public_id}/",
      path_params: ["event_public_id", "gate_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_timezone_timeline:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/timezone-timeline/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_timezone_timeline:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/timezone-timeline/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks_track_public_id:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/{track_public_id}/",
      path_params: [
        "event_public_id",
        "track_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_tracks_track_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/tracks/{track_public_id}/",
      path_params: [
        "event_public_id",
        "track_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "none",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  patch_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan:
    {
      method: "PATCH",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_abuse_signals:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/abuse-signals/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_abuse_signals_signal_public_id_resolve:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/abuse-signals/{signal_public_id}/resolve/",
      path_params: [
        "event_public_id",
        "signal_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_audit:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/audit/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_publish_results:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/publish-results/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_tokens:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/tokens/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_plan_tokens:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting-plan/tokens/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_candidates:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/candidates/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_request_email_token:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/request-email-token/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_results:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/results/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_status:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/status/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_voting_votes:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/voting/votes/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_workflow_presets:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/workflow-presets/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_events_event_public_id_workflow_presets_apply:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/workflow-presets/apply/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_inbox: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/inbox/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_inbox_recipient_public_id_read: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/inbox/{recipient_public_id}/read/",
    path_params: ["recipient_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_judge_directory: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/judge-directory/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_judge_events: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/judge-events/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_judge_expertise_judge_public_id: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/judge-expertise/{judge_public_id}/",
    path_params: ["judge_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  put_api_v1_workspaces_workspace_public_id_judge_expertise_judge_public_id: {
    method: "PUT",
    path: "/api/v1/workspaces/{workspace_public_id}/judge-expertise/{judge_public_id}/",
    path_params: ["judge_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_members: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/members/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_members: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/members/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_my_judge_expertise: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/my-judge-expertise/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  put_api_v1_workspaces_workspace_public_id_my_judge_expertise: {
    method: "PUT",
    path: "/api/v1/workspaces/{workspace_public_id}/my-judge-expertise/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_my_judge_invitations: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/my-judge-invitations/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_my_judge_invitations_invitation_public_id_respond:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/my-judge-invitations/{invitation_public_id}/respond/",
      path_params: ["invitation_public_id", "workspace_public_id"],
      query_params: [],
      request_body: true,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_operator_console: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/operator-console/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_participant_events: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/participant-events/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_taxonomies: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/taxonomies/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_taxonomies: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/taxonomies/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/taxonomies/{taxonomy_public_id}/",
    path_params: ["taxonomy_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id: {
    method: "PATCH",
    path: "/api/v1/workspaces/{workspace_public_id}/taxonomies/{taxonomy_public_id}/",
    path_params: ["taxonomy_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  delete_api_v1_workspaces_workspace_public_id_taxonomies_taxonomy_public_id: {
    method: "DELETE",
    path: "/api/v1/workspaces/{workspace_public_id}/taxonomies/{taxonomy_public_id}/",
    path_params: ["taxonomy_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "none",
  },
  get_api_v1_workspaces_workspace_public_id_webhooks: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/webhooks/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
  },
  post_api_v1_workspaces_workspace_public_id_webhooks: {
    method: "POST",
    path: "/api/v1/workspaces/{workspace_public_id}/webhooks/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  patch_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id: {
    method: "PATCH",
    path: "/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/",
    path_params: ["subscription_public_id", "workspace_public_id"],
    query_params: [],
    request_body: true,
    response_kind: "json",
  },
  get_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/deliveries/",
      path_params: ["subscription_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  get_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries_delivery_public_id:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/deliveries/{delivery_public_id}/",
      path_params: [
        "delivery_public_id",
        "subscription_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
  post_api_v1_workspaces_workspace_public_id_webhooks_subscription_public_id_deliveries_delivery_public_id_replay:
    {
      method: "POST",
      path: "/api/v1/workspaces/{workspace_public_id}/webhooks/{subscription_public_id}/deliveries/{delivery_public_id}/replay/",
      path_params: [
        "delivery_public_id",
        "subscription_public_id",
        "workspace_public_id",
      ],
      query_params: [],
      request_body: false,
      response_kind: "json",
    },
} as const;
