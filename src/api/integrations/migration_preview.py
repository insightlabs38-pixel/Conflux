"""Import preflight using the canonical importer inside a rolled-back transaction."""

from django.core.exceptions import ValidationError
from django.db import transaction

from .archive import FORMAT_VERSION, SECTION_KEYS, build_archive, import_archive


def preview_archive_import(*, workspace, archive, name, slug):
    if not isinstance(archive, dict):
        raise ValidationError({"archive": "Archive must be an object."})
    if type(archive.get("format_version")) is not int or archive.get("format_version") not in (
        FORMAT_VERSION,
        2,
        3,
        4,
    ):
        raise ValidationError(
            {
                "format_version": (
                    f"Unsupported archive format_version: {archive.get('format_version')!r}. "
                    "This build reads v1 config/full and v2/v3/v4 final; "
                    "older final archives re-export as v4; "
                    "no migration path for other versions."
                )
            }
        )

    with transaction.atomic():
        event = import_archive(workspace=workspace, archive=archive, name=name, slug=slug)
        imported = build_archive(event, mode=archive["mode"])
        transaction.set_rollback(True)

    source_event = (
        archive["event"]["fields"] if archive["format_version"] in (2, 3, 4) else archive["event"]
    )
    imported_event = (
        imported["event"]["fields"] if archive["format_version"] in (2, 3, 4) else imported["event"]
    )
    event_changes = [
        {"field": field, "source": source_event.get(field), "imported": imported_event[field]}
        for field in ("name", "slug", "status", "is_public")
        if source_event.get(field) != imported_event[field]
    ]
    sections = [
        {
            "section": key,
            "source_count": len(archive[key]),
            "imported_count": len(imported.get(key, [])),
        }
        for key in (*SECTION_KEYS, "projects")
        if key in archive
    ]
    ignored_sections = sorted(
        set(archive) - {"format_version", "mode", "event", *SECTION_KEYS, "projects"}
    )
    if archive["format_version"] in (2, 3, 4):
        sections = [
            {
                "section": label,
                "source_count": len(rows),
                "imported_count": len(imported["tables"][label]),
            }
            for label, rows in archive["tables"].items()
        ]
        ignored_sections = []
    return {
        "format_version": archive["format_version"],
        "mode": archive["mode"],
        "migration_steps": (
            ["v2 → v3: add empty award-resource table"] if archive["format_version"] == 2 else []
        )
        + (
            ["v3 → v4: add default event theme settings"]
            if archive["format_version"] in (2, 3)
            else []
        ),
        "deprecations": [],
        "event_changes": event_changes,
        "sections": sections,
        "ignored_sections": ignored_sections,
    }
