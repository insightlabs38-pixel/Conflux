"""Judging: rubric versions and the assignment solver (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features

manifest.register_capability(
    manifest.Capability(
        "assignment_strategy",
        "Assignment strategy",
        "How judges are paired with projects (`evaluations.assignment`); a choice inside one "
        "computation, so declared only.",
    )
)
manifest.register_manifest(
    manifest.Manifest(
        id="evaluations",
        version="1.0.0",
        label="Judging",
        provides=(
            ("feature", "evaluation_plan"),
            ("assignment_strategy", "heuristic"),
            ("assignment_strategy", "optimized"),
            ("version_source", "rubric"),
        ),
        requires=(("manifest", "core"),),
    )
)
