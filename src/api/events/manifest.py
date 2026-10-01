"""Event applications as an entity and a thread subject (EXTENSION_MANIFEST)."""

from core import manifest

manifest.register_manifest(
    manifest.Manifest(
        id="events",
        version="1.0.0",
        label="Events and applications",
        provides=(("entity", "applications"), ("thread_subject", "application")),
        requires=(("manifest", "core"),),
    )
)
