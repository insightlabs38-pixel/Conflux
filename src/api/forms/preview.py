"""Previewing a saved form as a person, at a version or as of a time (PREVIEW_CONTEXT,
PD-F002-B03-T01). Which fields a kind of person is shown is the form's own rule
(`validation.field_in_scope`); this only lays the answer out for an organizer. Read-only."""

from core import preview_context

from .validation import field_in_scope

ROLES = ("participant", "judge", "organizer", "public")


def _row(field):
    return {
        "id": field["id"],
        "label": field.get("label", field["id"]),
        "type": field.get("type", "text"),
        "options": field.get("options"),
        "required": bool(field.get("required", False)),
        "required_if": field.get("required_if"),
        "visible_to": sorted(field.get("visible_to", ["participant", "judge", "organizer"])),
        "visible_if": field.get("visible_if"),
    }


def resolve(user, workspace, ref, resolved, values):
    """Without a role the organizer sees the whole form; with one, only what that person is shown.
    A field that depends on an answer is kept and carries its condition, because the answer is not
    known here."""
    fields = (resolved.value or {}).get("fields", [])
    shown = [f for f in fields if resolved.role is None or field_in_scope(f, resolved.role)]
    return {
        "fields": [_row(f) for f in shown],
        "total": len(fields),
        "hidden": len(fields) - len(shown),
    }


def register():
    preview_context.register_surface(
        preview_context.Surface(
            key="form",
            label="Application form",
            params=("event", "form"),
            resolve=resolve,
            roles=ROLES,
            version_source="form",
        )
    )
