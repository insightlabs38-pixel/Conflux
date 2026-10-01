"""Bulk actions, the message approval policy and notification categories (EXTENSION_MANIFEST)."""

from core import manifest

from .bulk import ACTIONS

manifest.register_capability(
    manifest.Capability(
        "bulk_action",
        "Bulk action",
        "An operation planned and applied to many rows at once (`communications.bulk`).",
        lambda: {key: action.label for key, action in ACTIONS.items()},
    )
)
manifest.register_manifest(
    manifest.Manifest(
        id="communications",
        version="1.0.0",
        label="Communications",
        provides=(
            *(("bulk_action", key) for key in ("advance", "assign", "extend", "move", "send")),
            ("approval_policy", "message_send"),
            ("notification_category", "announcement"),
            ("notification_category", "essential"),
            ("notification_category", "mention"),
        ),
        requires=(("manifest", "core"),),
    )
)
