"""Create an event from a preset (PD-F001-B01).

Everything is written through the same domain models and validators the rest of the product uses,
so the result is an ordinary event: nothing is flagged "preset" except the `EventProfile`
provenance row. Must run inside the caller's transaction (it audits the rubric publications).
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from audit.services import record_mutation
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from eligibility.models import EligibilityRules
from evaluations.models import EvaluationPlan, RubricVersion
from events.models import Event, EventRegistrationSettings, RegistrationMode, Track
from stages.models import ParticipationMode, Stage, StageTransition

from .models import EventProfile
from .presets import get_preset

_SLUG_ATTEMPTS = 5


def _saved(instance):
    instance.full_clean()
    instance.save()
    return instance


def _timezone(name):
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise ValidationError({"timezone": f"Unknown time zone: {name!r}."}) from exc
    return name


def _ends_at(starts_at, zone, duration):
    """The end keeps the organizer's wall-clock time: a 28-day grant that starts at 10:00 local ends
    at 10:00 local even when a DST change falls inside the window (plain UTC arithmetic would end
    it an hour off)."""
    return (starts_at.astimezone(zone) + duration).astimezone(UTC)


def derive_event_slug(workspace, name):
    """The address an event gets when the organizer does not choose one: the name, slugified, and
    made unique in the workspace with a numeric suffix (spring-hack, spring-hack-2, ...)."""
    stem = (slugify(name) or "event")[:190].strip("-") or "event"
    taken = set(
        Event.objects.filter(workspace=workspace, slug__startswith=stem).values_list(
            "slug", flat=True
        )
    )
    candidate, number = stem, 1
    while candidate in taken:
        number += 1
        candidate = f"{stem}-{number}"
    return candidate


def create_event_from_preset(
    *,
    workspace,
    actor,
    preset_key,
    name,
    slug=None,
    starts_at: datetime | None = None,
    timezone: str = "UTC",
    registration_mode: str | None = None,
    min_team_size: int | None = None,
    max_team_size: int | None = None,
    is_public: bool = False,
):
    """A draft event whose configuration is complete except for what only the organizer knows.

    With `starts_at` the end is derived from the preset's duration. Registration mode and team
    size range, plus whether the event page is public, are the base decisions an organizer commonly
    changes at creation; everything else starts at the preset's value and is overridden later
    through the normal domain writes.
    """
    preset = get_preset(preset_key)
    if preset is None:
        raise ValidationError({"preset": "Unknown event preset."})
    if registration_mode is not None and registration_mode not in RegistrationMode.values:
        raise ValidationError({"registration_mode": "Unknown registration mode."})

    zone_name = _timezone(timezone)
    derived = not slug
    for attempt in range(_SLUG_ATTEMPTS):
        slug = slug or derive_event_slug(workspace, name)
        try:
            # A savepoint: losing a race for the address must not poison the caller's transaction.
            with transaction.atomic():
                event = _saved(
                    Event(
                        workspace=workspace,
                        name=name,
                        slug=slug,
                        description=preset.description,
                        timezone=zone_name,
                        is_public=is_public,
                        starts_at=starts_at,
                        ends_at=_ends_at(starts_at, ZoneInfo(zone_name), preset.duration)
                        if starts_at
                        else None,
                    )
                )
            break
        except IntegrityError as exc:
            if not derived or attempt == _SLUG_ATTEMPTS - 1:
                raise ValidationError(
                    {"slug": "That address was taken while the event was created; choose another."}
                ) from exc
            slug = None  # someone else took the derived address first: derive the next free one
    _saved(
        EventRegistrationSettings(event=event, mode=registration_mode or preset.registration_mode)
    )
    _saved(
        EligibilityRules(
            event=event,
            min_team_size=min_team_size if min_team_size is not None else preset.min_team_size,
            max_team_size=max_team_size if max_team_size is not None else preset.max_team_size,
            required_artifact_kinds=[str(kind) for kind in preset.required_artifact_kinds],
            require_finalized_submission=preset.require_finalized_submission,
        )
    )
    for position, track_name in enumerate(preset.tracks):
        _saved(Track(event=event, name=track_name, position=position))

    stages = [
        _saved(
            Stage(
                event=event,
                name=stage_name,
                position=position,
                is_initial=position == 0,
                participation_mode=(
                    ParticipationMode.TEAM_FORMATION
                    if position == 0
                    else ParticipationMode.TEAM_LOCKED
                ),
            )
        )
        for position, stage_name in enumerate(preset.stages)
    ]
    for before, after in zip(stages, stages[1:]):
        _saved(StageTransition(from_stage=before, to_stage=after))

    criteria = [criterion.as_json() for criterion in preset.criteria]
    for index in preset.judging_stages:
        plan = _saved(
            EvaluationPlan(
                stage=stages[index],
                name=f"{stages[index].name} judging",
                draft_criteria=criteria,
            )
        )
        # The rubric is part of the format, so it starts published: judges can be invited without
        # the organizer re-entering criteria. Editing it later publishes a new immutable version.
        version = RubricVersion.objects.create(plan=plan, number=1, criteria=plan.draft_criteria)
        record_mutation(
            actor=actor,
            workspace=workspace,
            action="rubric.published",
            target=version,
            metadata={"event_id": str(event.public_id), "preset": preset.key},
        )

    EventProfile.objects.create(event=event, preset_key=preset.key, preset_version=preset.version)
    return event
