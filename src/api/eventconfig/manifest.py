"""What each domain puts on the event timeline (EXTENSION_MANIFEST)."""

from core import manifest

manifest.register_manifest(
    manifest.Manifest(
        id="eventconfig",
        version="1.0.0",
        label="Event configuration",
        provides=tuple(
            ("timeline_provider", key)
            for key in (
                "agenda",
                "event",
                "gate",
                "office_hours",
                "publication",
                "reminder",
                "voting",
            )
        ),
        requires=(("manifest", "core"),),
    )
)
