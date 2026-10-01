"""What awards provides (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features

manifest.register_manifest(
    manifest.Manifest(
        id="awards",
        version="1.0.0",
        label="Awards",
        provides=(("feature", "award"),),
        requires=(("manifest", "core"),),
    )
)
