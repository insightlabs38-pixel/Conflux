"""Projects as an entity and a thread subject (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features

manifest.register_manifest(
    manifest.Manifest(
        id="projects",
        version="1.0.0",
        label="Projects",
        provides=(
            ("feature", "project"),
            ("feature", "submission"),
            ("entity", "projects"),
            ("thread_subject", "project"),
        ),
        requires=(("manifest", "core"),),
    )
)
