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
