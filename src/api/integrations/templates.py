"""Event templates and direct cloning (TPL-001..003), built on the same
canonical archive (PORT-001..004) that backs export/import: a template is
just a config-mode archive saved under a name, and cloning is building one
and importing it in the same call without ever persisting it.
"""

from django.core.exceptions import ValidationError

from .archive import SECTION_KEYS, build_archive, import_archive
from .models import EventTemplate


def clean_sections(sections):
    if sections is None:
        return list(SECTION_KEYS)
    unknown = set(sections) - set(SECTION_KEYS)
    if unknown:
        raise ValidationError({"sections": f"Unknown section(s): {', '.join(sorted(unknown))}."})
    return list(sections)


def save_template(*, event, name, actor, sections=None):
    sections = clean_sections(sections)
    archive = build_archive(event, mode="config", sections=sections)
    template = EventTemplate(
        workspace=event.workspace,
        name=name,
        source_event_name=event.name,
        sections=sorted(sections),
        archive=archive,
        created_by=actor,
    )
    template.full_clean()
    template.save()
    return template


def instantiate_template(*, template, workspace, name, slug):
    """Must run inside the caller's transaction -- same contract as
    `import_archive` itself, which this simply delegates to.
    """
    return import_archive(workspace=workspace, archive=template.archive, name=name, slug=slug)


def clone_event(*, event, name, slug, sections=None):
    """Must run inside the caller's transaction (see `instantiate_template`)."""
    sections = clean_sections(sections)
    archive = build_archive(event, mode="config", sections=sections)
    return import_archive(workspace=event.workspace, archive=archive, name=name, slug=slug)
