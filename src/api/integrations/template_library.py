"""Offline starter configurations: the event format presets of `eventconfig`.

Kept as the stable entry point of the template-library endpoints; the formats themselves, their
versions and how an event is built from one live in `eventconfig` (PD-F001-B01).
"""

from django.core.exceptions import ValidationError
from eventconfig.presets import PRESETS
from eventconfig.services import create_event_from_preset


def list_library():
    return [
        {
            "slug": preset.key,
            "version": preset.version,
            "label": preset.label,
            "description": preset.description,
            "tracks": list(preset.tracks),
            "stages": list(preset.stages),
            "duration_days": preset.duration_days,
            "registration_mode": str(preset.registration_mode),
            "min_team_size": preset.min_team_size,
            "max_team_size": preset.max_team_size,
            "required_artifact_kinds": [str(kind) for kind in preset.required_artifact_kinds],
            "criteria": [criterion.name for criterion in preset.criteria],
        }
        for preset in PRESETS.values()
    ]


def instantiate_library_template(*, workspace, template_slug, name, slug, actor=None, **options):
    """Build an editable draft; the caller wraps all rows in one transaction."""
    if template_slug not in PRESETS:
        raise ValidationError({"template": "Unknown local template."})
    return create_event_from_preset(
        workspace=workspace,
        actor=actor,
        preset_key=template_slug,
        name=name,
        slug=slug,
        **options,
    )
