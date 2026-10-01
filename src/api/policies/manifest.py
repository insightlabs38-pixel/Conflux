"""What policies provides (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features

manifest.register_manifest(
    manifest.Manifest(
        id="policies",
        version="1.0.0",
        label="Policies",
        provides=(("feature", "policy"),),
        requires=(("manifest", "core"),),
    )
)
