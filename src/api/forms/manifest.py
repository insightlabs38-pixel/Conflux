"""Form versions (EXTENSION_MANIFEST)."""

from core import manifest

manifest.register_manifest(
    manifest.Manifest(
        id="forms",
        version="1.0.0",
        label="Forms",
        provides=(("version_source", "form"),),
        requires=(("manifest", "core"),),
    )
)
