"""Form versions and the form preview (EXTENSION_MANIFEST)."""

from core import manifest

manifest.register_manifest(
    manifest.Manifest(
        id="forms",
        version="1.0.0",
        label="Forms",
        provides=(("version_source", "form"), ("preview_surface", "form")),
        requires=(("manifest", "core"),),
    )
)
