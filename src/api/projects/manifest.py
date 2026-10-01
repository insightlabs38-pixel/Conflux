"""Projects as an entity and a thread subject (EXTENSION_MANIFEST)."""

from core import manifest

manifest.register_manifest(
    manifest.Manifest(
        id="projects",
        version="1.0.0",
        label="Projects",
        provides=(("entity", "projects"), ("thread_subject", "project")),
        requires=(("manifest", "core"),),
    )
)
