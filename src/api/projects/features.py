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
                "own:project_member",
                "test:tests/integration/test_submission_reopen_diff.py::test_reopen_service_rejects_non_organizers_without_changing_history",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
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
