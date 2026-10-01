"""What participation provides (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features

manifest.register_manifest(
    manifest.Manifest(
        id="participation",
        version="1.0.0",
        label="Participation",
        provides=(("feature", "team"),),
        requires=(("manifest", "core"),),
    )
)
