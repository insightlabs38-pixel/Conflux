"""Features of projects (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="project",
        label="Project",
        model="projects.Project",
        claims={"identity": provided("field:public_id", "route:project-detail")},
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
        claims={"identity": provided("field:public_id", "route:submission-detail")},
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
