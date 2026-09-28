"""Frozen v2 final-archive tables; new fields require an explicit contract change."""

TABLES = {
    "events.track": ("event", "event name description position", ""),
    "events.baseprize": ("event", "event track name description kind amount currency position", ""),
    "stages.stage": ("event", "event name position is_initial participation_mode created_at", ""),
    "stages.stagetransition": ("from_stage__event", "from_stage to_stage created_at", ""),
    "participation.team": ("event", "event name created_at", ""),
    "participation.teammembership": ("team__event", "team user role joined_at", ""),
    "projects.project": (
        "event",
        "event team track name description created_by created_at updated_at",
        "",
    ),
    "projects.projectmembership": ("project__event", "project user role joined_at", ""),
    "stages.stageentry": ("stage__event", "stage subject_type subject_id entered_at exited_at", ""),
    "forms.formdefinition": ("event", "event stage name draft_schema created_at updated_at", ""),
    "forms.formversion": ("definition__event", "definition number schema published_at", ""),
    "forms.formresponse": (
        "project__event",
        "project version updated_by created_at updated_at",
        "",
    ),
    "forms.formanswer": ("response__project__event", "response field_id value", ""),
    "artifacts.artifact": (
        "project__event",
        "project kind visibility title external_url object_key content_type byte_size "
        "sha256 status created_by created_at updated_at",
        "",
    ),
    "artifacts.artifactvalidation": (
        "artifact__project__event",
        "artifact validator outcome detail checked_at",
        "",
    ),
    "projects.submission": (
        "project__event",
        "project stage status draft_payload draft_revision current_version updated_by "
        "created_at updated_at",
        "",
    ),
    "projects.submissionversion": (
        "submission__project__event",
        "submission number snapshot digest finalized_by finalized_at",
        "",
    ),
    "policies.policy": ("event", "event name ast created_at updated_at", ""),
    "policies.temporalgate": ("event", "event name opens_at closes_at created_at", ""),
    "policies.policybinding": ("event", "event action policy created_at", ""),
    "evaluations.evaluationpool": ("event", "event name created_at", ""),
    "evaluations.poolmembership": ("pool__event", "pool judge created_at", "track_expertise"),
    "evaluations.evaluationplan": (
        "stage__event",
        "stage name candidate_type pool_strategy mode results_visible_to_participants "
        "feedback_visible_to_participants feedback_anonymous draft_criteria pool "
        "active_assignment_version published_normalization_run published_pairwise_run "
        "tie_breaks calibration_required blind_judging prize_judging hybrid_source "
        "created_at updated_at",
        "calibration_projects",
    ),
    "evaluations.rubricversion": ("plan__stage__event", "plan number criteria published_at", ""),
    "evaluations.conflictofinterest": (
        "event",
        "event judge project reason declared_by created_at",
        "",
    ),
    "evaluations.assignmentversion": (
        "plan__stage__event",
        "plan number coverage evidence created_at",
        "",
    ),
    "evaluations.assignment": ("version__plan__stage__event", "version judge project", ""),
    "evaluations.ballot": (
        "rubric_version__plan__stage__event",
        "rubric_version judge project comment is_calibration submitted_at",
        "",
    ),
    "evaluations.ballotresponse": ("ballot__project__event", "ballot criterion_id score", ""),
    "evaluations.normalizationrun": (
        "plan__stage__event",
        "plan number ridge_lambda iterations converged grand_mean evidence created_at",
        "",
    ),
    "evaluations.pairwisecomparison": (
        "plan__stage__event",
        "plan judge project_a project_b winner submitted_at",
        "",
    ),
    "evaluations.pairwiserun": (
        "plan__stage__event",
        "plan number prior_games iterations converged evidence created_at",
        "",
    ),
    "awards.award": (
        "event",
        "event name description eligibility_track require_finalized_submission "
        "selection_source evaluation_plan winner_count allow_stacking conflict_group "
        "published_at created_at",
        "",
    ),
    "awards.prizepackage": ("award__event", "award name", ""),
    "awards.prizecomponent": (
        "package__award__event",
        "package kind name description quantity amount currency position",
        "",
    ),
    "awards.awardwinner": (
        "award__event",
        "award project selected_by source evidence override_reason selected_at",
        "",
    ),
    "awards.prizefulfillment": (
        "winner__award__event",
        "winner component state note updated_by updated_at",
        "",
    ),
    "community.votingplan": (
        "event",
        "event identity_mode opens_at closes_at allow_comments comment_visibility "
        "results_published_at created_at updated_at",
        "",
    ),
    "community.vote": ("plan__event", "plan project voter_key cast_at", ""),
    "presentation.page": ("event", "event theme created_at updated_at", ""),
    "presentation.pageblock": (
        "page__event",
        "page kind position config created_at updated_at",
        "",
    ),
    "presentation.publicationschedule": (
        "event",
        "event surface opens_at closes_at finalist_stage updated_at",
        "",
    ),
    "eligibility.eligibilityrules": (
        "event",
        "event min_team_size max_team_size required_artifact_kinds require_finalized_submission "
        "require_track require_clearance updated_at",
        "",
    ),
    "eligibility.eligibilityreview": (
        "project__event",
        "project status decision_note decided_by decided_at revision created_at updated_at",
        "",
    ),
    "eligibility.eligibilityfinding": (
        "review__project__event",
        "review code automated severity message state participant_response responded_by "
        "resolution_note closed_by opened_at addressed_at closed_at",
        "",
    ),
    "deliberation.deliberationroom": (
        "award__event",
        "award status quorum opened_by opened_at closed_at finalized_at finalization",
        "",
    ),
    "deliberation.deliberationnote": (
        "room__award__event",
        "room project author body created_at",
        "",
    ),
    "deliberation.deliberationstance": (
        "room__award__event",
        "room judge project stance rationale updated_at",
        "",
    ),
    "onsite.location": ("event", "event kind name parent capacity x y notes position", ""),
    "onsite.projectlocation": ("project__event", "project location assigned_at", ""),
}
