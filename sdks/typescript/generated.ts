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
  tracks: Record<string, unknown>[];
  base_prizes: Record<string, unknown>[];
  stages: Record<string, unknown>[];
  stage_transitions: Record<string, unknown>[];
  forms: Record<string, unknown>[];
  policies: Record<string, unknown>[];
  temporal_gates: Record<string, unknown>[];
  policy_bindings: Record<string, unknown>[];
  awards: Record<string, unknown>[];
  projects?: Record<string, unknown>[];
};

export type InputOfArchiveOutput = {
  format_version: number;
  mode: string;
  event: Record<string, unknown>;
  tracks: Record<string, unknown>[];
  base_prizes: Record<string, unknown>[];
  stages: Record<string, unknown>[];
  stage_transitions: Record<string, unknown>[];
  forms: Record<string, unknown>[];
  policies: Record<string, unknown>[];
  temporal_gates: Record<string, unknown>[];
  policy_bindings: Record<string, unknown>[];
  awards: Record<string, unknown>[];
  projects?: Record<string, unknown>[];
};

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

export type ConflictOfInterest = {
  public_id: string;
  judge: string;
  project: string;
  reason?: string;
  created_at: string;
};

export type InputOfConflictOfInterest = { reason?: string };

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
  mode?: ModeEnum;
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
  mode?: InputOfModeEnum;
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

export type JudgeEventSummary = { public_id: string; name: string };

export type InputOfJudgeEventSummary = { public_id: string; name: string };

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

export type LoginInputSchema = { username: string; password: string };

export type InputOfLoginInputSchema = { username: string; password: string };

export type LoginResponseSchema = { user: UserSummarySchema };

export type InputOfLoginResponseSchema = { user: InputOfUserSummarySchema };

export type MarketplaceProfileInput = {
  skills: string[];
  bio?: string;
  visible: boolean;
};

export type InputOfMarketplaceProfileInput = {
  skills: string[];
  bio?: string;
  visible: boolean;
};

export type MarketplaceProfileSchema = {
  public_id: string;
  user: string;
  username: string;
  skills: string[];
  bio: string;
  visible: boolean;
  matched_skills?: string[];
};

export type InputOfMarketplaceProfileSchema = {
  public_id: string;
  user: string;
  username: string;
  skills: string[];
  bio: string;
  visible: boolean;
  matched_skills?: string[];
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

export type ModeEnum = "rubric" | "pairwise";

export type InputOfModeEnum = "rubric" | "pairwise";

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
  mode?: ModeEnum;
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
  mode?: InputOfModeEnum;
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

export type PatchedFulfillmentInput = { state?: StateEnum; note?: string };

export type InputOfPatchedFulfillmentInput = {
  state?: InputOfStateEnum;
  note?: string;
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

export type PatchedSubscriptionUpdate = { enabled?: boolean };

export type InputOfPatchedSubscriptionUpdate = { enabled?: boolean };

export type PatchedTeamOpeningInput = {
  title?: string;
  description?: string;
  desired_skills?: string[];
  project?: string | null;
  is_open?: boolean;
};

export type InputOfPatchedTeamOpeningInput = {
  title?: string;
  description?: string;
  desired_skills?: string[];
  project?: string | null;
  is_open?: boolean;
};

export type PatchedTemporalGate = {
  public_id?: string;
  name?: string;
  opens_at?: string | null;
  closes_at?: string | null;
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

export type ResultsPublishInputSchema = {
  normalization_run: string;
  tie_breaks?: Record<string, number>;
};

export type InputOfResultsPublishInputSchema = {
  normalization_run: string;
  tie_breaks?: Record<string, number>;
};

export type RubricVersion = {
  public_id: string;
  number: number;
  criteria: unknown;
  published_at: string;
};

export type InputOfRubricVersion = { number: number; criteria: unknown };

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

export type StateEnum =
  "pending" | "contacted" | "verified" | "sent" | "claimed" | "failed";

export type InputOfStateEnum =
  "pending" | "contacted" | "verified" | "sent" | "claimed" | "failed";

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
  project?: string | null;
  is_open?: boolean;
};

export type InputOfTeamOpeningInput = {
  title: string;
  description?: string;
  desired_skills: string[];
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
  is_open: boolean;
  matched_skills: string[];
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
  is_open: boolean;
  matched_skills: string[];
};

export type TemporalGate = {
  public_id: string;
  name: string;
  opens_at?: string | null;
  closes_at?: string | null;
  created_at: string;
};

export type InputOfTemporalGate = {
  name: string;
  opens_at?: string | null;
  closes_at?: string | null;
};

export type ThemeEnum = "default" | "dark" | "minimal";

export type InputOfThemeEnum = "default" | "dark" | "minimal";

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
  get_api_v1_audit_workspace_public_id: {
    request: { path: { workspace_public_id: string } };
    response: AuditEventSchema[];
  };
  get_api_v1_audit_workspace_public_id_events_event_public_id_config_history: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ConfigHistoryEntrySchema[];
  };
  get_api_v1_events_event_public_id: {
    request: { path: { event_public_id: string } };
    response: PublicEventSchema;
  };
  get_api_v1_events_event_public_id_awards: {
    request: { path: { event_public_id: string } };
    response: PublicAwardOutput[];
  };
  get_api_v1_events_event_public_id_gallery: {
    request: { path: { event_public_id: string } };
    response: GalleryItemOutput[];
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
    request: {
      query?: {
        format?: "json" | "yaml";
        lang?:
          | "af"
          | "ar"
          | "ar-dz"
          | "ast"
          | "az"
          | "be"
          | "bg"
          | "bn"
          | "br"
          | "bs"
          | "ca"
          | "ckb"
          | "cs"
          | "cy"
          | "da"
          | "de"
          | "dsb"
          | "el"
          | "en"
          | "en-au"
          | "en-gb"
          | "eo"
          | "es"
          | "es-ar"
          | "es-co"
          | "es-mx"
          | "es-ni"
          | "es-ve"
          | "et"
          | "eu"
          | "fa"
          | "fi"
          | "fr"
          | "fy"
          | "ga"
          | "gd"
          | "gl"
          | "he"
          | "hi"
          | "hr"
          | "hsb"
          | "hu"
          | "hy"
          | "ia"
          | "id"
          | "ig"
          | "io"
          | "is"
          | "it"
          | "ja"
          | "ka"
          | "kab"
          | "kk"
          | "km"
          | "kn"
          | "ko"
          | "ky"
          | "lb"
          | "lt"
          | "lv"
          | "mk"
          | "ml"
          | "mn"
          | "mr"
          | "ms"
          | "my"
          | "nb"
          | "ne"
          | "nl"
          | "nn"
          | "os"
          | "pa"
          | "pl"
          | "pt"
          | "pt-br"
          | "ro"
          | "ru"
          | "sk"
          | "sl"
          | "sq"
          | "sr"
          | "sr-latn"
          | "sv"
          | "sw"
          | "ta"
          | "te"
          | "tg"
          | "th"
          | "tk"
          | "tr"
          | "tt"
          | "udm"
          | "ug"
          | "uk"
          | "ur"
          | "uz"
          | "vi"
          | "zh-hans"
          | "zh-hant";
      };
    };
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
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: ArchiveOutput;
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
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_workload: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: JudgeWorkloadRowSchema[];
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
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_checklist: {
    request: { path: { event_public_id: string; workspace_public_id: string } };
    response: LaunchChecklistSchema;
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
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates_gate_public_id: {
    request: {
      path: {
        event_public_id: string;
        gate_public_id: string;
        workspace_public_id: string;
      };
    };
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
  get_api_v1_workspaces_workspace_public_id_judge_events: {
    request: { path: { workspace_public_id: string } };
    response: JudgeEventSummary[];
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
  get_api_v1_workspaces_workspace_public_id_participant_events: {
    request: { path: { workspace_public_id: string } };
    response: ParticipantEventSummary[];
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
  get_api_v1_events_event_public_id: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/",
    path_params: ["event_public_id"],
    query_params: [],
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
  get_api_v1_events_event_public_id_gallery: {
    method: "GET",
    path: "/api/v1/events/{event_public_id}/gallery/",
    path_params: ["event_public_id"],
    query_params: [],
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
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_archive: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/archive/",
    path_params: ["event_public_id", "workspace_public_id"],
    query_params: [],
    request_body: false,
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
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_judge_workload:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/judge-workload/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
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
  get_api_v1_workspaces_workspace_public_id_events_event_public_id_operations_checklist:
    {
      method: "GET",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/operations/checklist/",
      path_params: ["event_public_id", "workspace_public_id"],
      query_params: [],
      request_body: false,
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
  delete_api_v1_workspaces_workspace_public_id_events_event_public_id_temporal_gates_gate_public_id:
    {
      method: "DELETE",
      path: "/api/v1/workspaces/{workspace_public_id}/events/{event_public_id}/temporal-gates/{gate_public_id}/",
      path_params: ["event_public_id", "gate_public_id", "workspace_public_id"],
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
  get_api_v1_workspaces_workspace_public_id_judge_events: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/judge-events/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
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
  get_api_v1_workspaces_workspace_public_id_participant_events: {
    method: "GET",
    path: "/api/v1/workspaces/{workspace_public_id}/participant-events/",
    path_params: ["workspace_public_id"],
    query_params: [],
    request_body: false,
    response_kind: "json",
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
