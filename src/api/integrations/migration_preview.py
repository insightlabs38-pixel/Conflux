"""Import preflight using the canonical importer inside a rolled-back transaction."""

from django.core.exceptions import ValidationError
from django.db import transaction

from .archive import FORMAT_VERSION, SECTION_KEYS, build_archive, import_archive


def preview_archive_import(*, workspace, archive, name, slug):
    if not isinstance(archive, dict):
        raise ValidationError({"archive": "Archive must be an object."})
    if archive.get("format_version") != FORMAT_VERSION:
        raise ValidationError(
            {
                "format_version": (
                    f"Unsupported archive format_version: {archive.get('format_version')!r}. "
                    f"This build only reads version {FORMAT_VERSION}; no migration path is defined."
                )
            }
        )

    with transaction.atomic():
        event = import_archive(workspace=workspace, archive=archive, name=name, slug=slug)
        imported = build_archive(event, mode=archive["mode"])
        transaction.set_rollback(True)

    source_event = archive["event"]
    event_changes = [
        {"field": field, "source": source_event.get(field), "imported": imported["event"][field]}
        for field in ("name", "slug", "status", "is_public")
        if source_event.get(field) != imported["event"][field]
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
    return {
        "format_version": FORMAT_VERSION,
        "mode": archive["mode"],
        "migration_steps": [],
        "deprecations": [],
        "event_changes": event_changes,
        "sections": sections,
        "ignored_sections": ignored_sections,
    }
