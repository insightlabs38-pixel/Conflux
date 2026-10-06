"""Features of projects (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="project",
        label="Project",
        model="projects.Project",
        claims={
            "identity": provided("field:public_id", "route:project-detail"),
            "validation": provided(
                "check:projects.models.Project.clean",
                "test:tests/integration/test_project_identity.py::test_project_api_rejects_nonmember_and_missing_name",
            ),
            "authorization": provided(
                "route:project-list",
                "route:project-detail",
                "scope:event",
                "readers:members",
                "writers:members",
                "own:project_member",
                "test:tests/integration/test_project_identity.py::test_project_api_rejects_nonmember_and_missing_name",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:project-list:POST=project.created",
                "write:project-detail:PATCH=project.updated",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:project-list:POST=keyed",
                "mode:project-detail:PATCH=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
                "test:tests/integration/test_feature_idempotency.py::test_a_keyed_change_runs_once_for_one_key_and_a_different_body_is_refused",
            ),
            "rest": provided(
                "list:project-list",
                "detail:project-detail",
                "paging:unpaged@bounded: the list is the caller's own projects in one event;  "
                "every project is paged through the projects query entity",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "entity:projects",
                "fields:name,description,track,team,created_by,gallery_visible,gallery_blocked,created_at",
                "test:tests/integration/test_entity_query.py::test_every_registered_field_resolves_against_the_database",
            ),
            "ui_base": provided(
                "component:src/web/features/artifacts/ProjectWorkspace.tsx",
                "component:src/web/features/teams/TeamWorkspace.tsx",
                "test:src/web/features/artifacts/ProjectWorkspace.test.tsx",
            ),
            "ui_advanced": provided(
                "uses:EntityGrid@src/web/features/event-builder/ProjectsGrid.tsx",
                "uses:BulkPlanner@src/web/features/event-builder/ProjectsGrid.tsx",
                "uses:RichEditor@src/web/features/artifacts/ProjectStoryEditor.tsx",
            ),
            "bulk": provided(
                "action:move=project.track_moved",
                "test:tests/integration/test_bulk_operations.py::test_full_preview_apply_and_retry_are_atomic_and_audited",
            ),
            "cli": provided(
                "no_cli@projects are written by their teams and read on organizer grids; the "
                "CLI administers events only",
            ),
            "mcp": provided(
                "tool:list_my_projects",
                "tool:get_project",
                "test:tests/integration/test_mcp_adapter.py::test_a_read_tool_returns_real_data_and_is_audited_without_content",
                "test:tests/integration/test_feature_mcp.py::test_each_claimed_tool_reaches_its_own_route_with_a_credential_limited_to_it",
            ),
            "event_as_code": provided(
                "no_eac@projects are runtime participant data written by their teams",
            ),
            "webhook": provided(
                "silent:project.created@no event type exists for projects yet; a submission's "
                "finalization is the event subscribers get",
                "silent:project.updated@no event type exists for project edits; a submission's "
                "finalization is the event subscribers get",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "table:projects.project",
                "test:tests/integration/test_feature_archive.py::test_each_claimed_table_is_restored_with_its_rows",
            ),
            "analytics": provided(
                "section:submissions",
                "measure:submissions.projects",
                "measure:submissions.with_submission",
                "measure:submissions.finalized_projects",
                "test:tests/integration/test_feature_analytics.py::test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event",
            ),
            "privacy": provided(
                "retained:project_memberships",
                "retained:appeals",
                "retained:eligibility_responses",
                "erased:comments",
                "person:created_by=retained@a project is kept as evidence of the event and its "
                "creator is not rewritten",
                "test:tests/integration/test_feature_privacy.py::test_a_real_subject_is_exported_and_erased_as_every_claim_says",
            ),
            "extension": provided(
                "hook:entity=projects",
                "hook:thread_subject=projects",
                "test:tests/integration/test_feature_extension.py::test_every_hook_pair_is_claimed_once_and_the_manifests_agree_with_the_live_registries",
            ),
            "versioning": provided(
                "in_place@a project is edited in place; the finalized submission is its "
                "versioned record",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note="Created, edited and deleted in place; each stage's submission carries the state.",
        ),
    )
)
register_feature(
    Feature(
        key="submission",
        label="Submission",
        model="projects.Submission",
        claims={
            "identity": provided("field:public_id", "route:submission-detail"),
            "validation": provided(
                "check:projects.models.Submission.clean",
                "check:projects.submissions.finalize_submission",
                "constraint:projects.Submission.unique_project_stage_submission",
                "test:tests/integration/test_submission_reopen_diff.py::test_reopened_draft_cannot_be_saved_after_the_deadline",
            ),
            "authorization": provided(
                "route:submission-detail",
                "route:submission-finalize",
                "route:submission-reopen",
                "route:submission-stage-list",
                "route:submission-preview",
                "scope:event",
                "readers:members",
                "writers:members",
                "narrow:submission-reopen:POST=admin,organizer",
                "own:project_member",
                "test:tests/integration/test_submission_reopen_diff.py::test_reopen_service_rejects_non_organizers_without_changing_history",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:submission-detail:PUT=submission.draft_saved",
                "write:submission-finalize:POST=submission.finalized",
                "write:submission-reopen:POST=submission.reopened",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:submission-detail:PUT=locked@projects.Submission.draft_revision",
                "mode:submission-finalize:POST=natural",
                "mode:submission-reopen:POST=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:submission-stage-list",
                "detail:submission-detail",
                "paging:unpaged@bounded: a project has one submission per stage",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read per project and stage through its own routes; submissions are "
                "searched through the projects entity",
            ),
            "ui_base": provided(
                "component:src/web/features/submissions/SubmissionPanel.tsx",
                "test:src/web/features/submissions/SubmissionPanel.test.tsx",
            ),
            "ui_advanced": provided(
                "no_advanced@a submission is one draft and one final per stage, edited in the "
                "base screen; nothing sits beyond it yet",
            ),
            "bulk": provided(
                "no_bulk@a submission is one draft and one final per stage, written by its team "
                "and never in a batch",
            ),
            "cli": provided(
                "no_cli@submissions are written and finalized by their team; the CLI is an "
                "organizer tool for events only",
            ),
            "mcp": provided(
                "no_mcp@a submission is written and finalized by its team; agents read the "
                "project, not the submission",
            ),
            "event_as_code": provided(
                "no_eac@submissions are runtime participant data and are never touched by an apply",
            ),
            "webhook": provided(
                "silent:submission.draft_saved@a draft is private to its team until it is "
                "finalized, which subscribers do receive",
                "emit:submission.finalized=submission.finalized",
                "silent:submission.reopened@no event type exists for reopening yet; subscribers "
                "see the next finalization",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "table:projects.submission",
                "test:tests/integration/test_feature_archive.py::test_each_claimed_table_is_restored_with_its_rows",
            ),
            "analytics": provided(
                "section:submissions",
                "measure:submissions.draft_records",
                "measure:submissions.finalized_records",
                "measure:submissions.immutable_versions",
                "test:tests/integration/test_feature_analytics.py::test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event",
            ),
            "privacy": provided(
                "retained:submissions",
                "retained:submission_versions",
                "person:updated_by=retained@a finalized submission is evidence and its author "
                "is kept so it stays verifiable",
                "test:tests/integration/test_feature_privacy.py::test_a_real_subject_is_exported_and_erased_as_every_claim_says",
            ),
            "extension": provided(
                "no_extension@a submission is one fixed lifecycle; the extension points sit on "
                "the project",
            ),
            "versioning": provided(
                "immutable:projects.SubmissionVersion",
                "counter:draft_revision",
                "test:tests/integration/test_feature_versioning.py::test_each_claimed_version_model_refuses_an_edit_and_a_delete",
            ),
        },
        lifecycle=Lifecycle(
            "choice",
            field="status",
            initial=("draft",),
            transitions={"draft": ("finalized",), "finalized": ("draft",)},
            via=(
                "projects.submissions.finalize_submission",
                "projects.submissions.reopen_submission",
            ),
        ),
    )
)
