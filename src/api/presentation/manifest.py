"""Page blocks: what the public page builder offers (EXTENSION_MANIFEST)."""

from core import manifest

from .block_types import BLOCK_TYPES

manifest.register_capability(
    manifest.Capability(
        "page_block",
        "Page block",
        "A block an organizer can add to the public event page (`presentation.block_types`).",
        lambda: {key: block["title"] for key, block in BLOCK_TYPES.items()},
    )
)
manifest.register_manifest(
    manifest.Manifest(
        id="presentation",
        version="1.0.0",
        label="Public pages",
        provides=(("preview_surface", "page"),)
        + tuple(
            ("page_block", key)
            for key in (
                "announcements",
                "cta",
                "faq",
                "gallery",
                "hero",
                "lead",
                "prizes",
                "resources",
                "results",
                "rich_text",
                "schedule",
                "sponsors",
                "tracks",
            )
        ),
        requires=(("manifest", "core"),),
    )
)
