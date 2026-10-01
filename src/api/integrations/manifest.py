"""Background jobs and the archive formats this deployment reads and writes (EXTENSION_MANIFEST).

The archive converter and importer and exporter are code boundaries, not registries, so they are
declared only: listed, and requirements resolve against them, with nothing to verify them against.
"""

from core import manifest

for kind, label, description in (
    (
        "archive_exporter",
        "Archive exporter",
        "Writes an event as a canonical archive (`build_archive`).",
    ),
    (
        "archive_importer",
        "Archive importer",
        "Creates a private draft event from an archive (`import_archive`).",
    ),
    ("archive_converter", "Archive converter", "Maps another source into the canonical archive."),
):
    manifest.register_capability(manifest.Capability(kind, label, description))

manifest.register_manifest(
    manifest.Manifest(
        id="integrations",
        version="1.0.0",
        label="Archives and integrations",
        provides=(
            ("job_kind", "archive_export"),
            ("archive_exporter", "config"),
            ("archive_exporter", "full"),
            ("archive_exporter", "final"),
            ("archive_importer", "canonical"),
            ("archive_converter", "project_csv"),
        ),
        requires=(("manifest", "core"),),
    )
)
