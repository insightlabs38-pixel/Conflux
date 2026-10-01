"""Event applications as an entity and a thread subject (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features

manifest.register_manifest(
    manifest.Manifest(
        id="events",
        version="1.0.0",
        label="Events and applications",
        provides=(
            ("feature", "event"),
            ("feature", "track"),
            ("feature", "application"),
            ("feature", "announcement"),
            ("entity", "applications"),
            ("thread_subject", "application"),
        ),
        requires=(("manifest", "core"),),
    )
)
