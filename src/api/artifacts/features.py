"""Features of artifacts (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="artifact",
        label="Artifact",
        model="artifacts.Artifact",
        claims={
            "identity": provided("field:public_id", "route:artifact-detail"),
            "validation": provided(
                "check:artifacts.models.Artifact.clean",
                "check:artifacts.validators.validate_artifact",
                "test:tests/integration/test_artifact_api.py::test_external_artifact_api_rejects_bad_url_and_nonmember",
            ),
            "authorization": provided(
                "route:artifact-list",
                "route:artifact-detail",
                "route:artifact-upload-intent",
                "route:artifact-validate",
                "scope:event",
                "readers:members",
                "writers:members",
                "own:project_member",
                "test:tests/integration/test_artifact_upload.py::test_nonmember_cannot_issue_or_complete_upload",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:artifact-list:POST=artifact.added",
                "write:artifact-upload-intent:POST=artifact.upload_started",
                "write:artifact-validate:POST=artifact.validated",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:artifact-list:POST=keyed",
                "mode:artifact-upload-intent:POST=none@each call starts a new pending upload "
                "whose signed URL expires with its intent, so a stored response would hand "
                "back a dead URL",
                "mode:artifact-validate:POST=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
                "test:tests/integration/test_feature_idempotency.py::test_a_keyed_change_runs_once_for_one_key_and_a_different_body_is_refused",
            ),
            "rest": provided(
                "list:artifact-list",
                "detail:artifact-detail",
                "paging:unpaged@bounded: a project holds a few artifacts",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read per project through its own list; a project holds a few artifacts, "
                "so a query over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/artifacts/ArtifactPanel.tsx",
                "test:src/web/features/artifacts/ArtifactPanel.test.tsx",
            ),
        },
        lifecycle=Lifecycle(
            "choice",
            field="status",
            initial=("pending", "uploaded"),
            transitions={
                "pending": ("uploaded", "ready", "rejected", "purged"),
                "uploaded": ("ready", "rejected", "purged"),
                "ready": ("rejected", "purged"),
                "rejected": ("ready", "purged"),
            },
            terminal=("purged",),
            via=(
                "artifacts.services.complete_upload",
                "artifacts.validators.validate_artifact",
                "integrations.privacy.enforce_retention",
            ),
        ),
    )
)
