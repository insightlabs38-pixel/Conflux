"""The setting registry (PD-F001-B01): every configurable value of an event, described once.

The domain rows stay the only place a value lives; a `SettingSpec` says where to read it, what its
default and preset baseline are, which existing endpoint writes it and whether it is locked right
now. That is what makes defaults and derived values queryable, so automation and the UI never have
to reverse-engineer them. Nothing here writes; writes go through the domain endpoint named in
`write`, with its own validation, audit and versioning.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from artifacts.models import ArtifactKind
from eligibility.models import EligibilityRules
from events.models import Event, EventRegistrationSettings, EventStatus, RegistrationMode
from rest_framework import serializers

BASE, ADVANCED, EXPERT = "base", "advanced", "expert"
TIERS = (BASE, ADVANCED, EXPERT)

# Where a value comes from. `default`/`preset`/`overridden` compare it with its baseline;
# `set`/`unset` are for values only the organizer knows (name, dates); `derived` is computed.
SOURCES = ("default", "preset", "overridden", "set", "unset", "derived")


@dataclass(frozen=True)
class Lock:
    code: str
    message: str


@dataclass(frozen=True)
class Write:
    """The existing endpoint that changes a setting (path relative to /api/v1/)."""

    method: str
    path: str  # with {workspace} and {event}
    field: str
    body: str = "partial"  # "partial": send only this field; "whole": the endpoint replaces all


@dataclass(frozen=True)
class SettingSpec:
    key: str
    module: str
    tier: str
    label: str
    help: str
    schema: dict  # JSON-Schema-compatible descriptor of the value
    read: Callable[[Event], Any]
    default: Any = None
    write: Write | None = None  # None for derived values
    # Only the organizer can know it (name, dates): never "default" or "overridden".
    organizer_owned: bool = False
    derived: bool = False
    lock: Callable[[Event], Lock | None] | None = None
    # What a valid new value must satisfy beyond its type: text, or a function of the event for
    # rules that only apply in some states. A lock stops a change; a constraint shapes it.
    constraint: str | Callable[[Event], str | None] | None = None
    # Free-form marker used by tests and docs, e.g. which task introduced the entry.
    tags: tuple = field(default_factory=tuple)


_EVENT = Write("PATCH", "workspaces/{workspace}/events/{event}/", "")
_REGISTRATION = Write("PUT", "workspaces/{workspace}/events/{event}/registration-settings/", "")
_RULES = Write("PUT", "workspaces/{workspace}/events/{event}/eligibility-rules/", "", body="whole")


def _w(base: Write, field_name: str) -> Write:
    return Write(base.method, base.path, field_name, base.body)


def _registration(event):
    return (
        EventRegistrationSettings.objects.filter(event=event).first() or EventRegistrationSettings()
    )


def _rules(event):
    return EligibilityRules.objects.filter(event=event).first() or EligibilityRules()


def _iso(value):
    # The same wire format as the rest of the API (UTC as "Z"), so a value compares equal to what
    # the event endpoint returns and accepts.
    return serializers.DateTimeField().to_representation(value) if value else None


def _duration_hours(event):
    if not (event.starts_at and event.ends_at):
        return None
    return round((event.ends_at - event.starts_at).total_seconds() / 3600, 2)


def _open_dates_constraint(event):
    if event.status == EventStatus.OPEN:
        return "Both dates are required while the event is open, and the end must be in the future."
    return None


def _starts_constraint(event):
    return "Must be before the end when both are set. " + (_open_dates_constraint(event) or "")


def _ends_constraint(event):
    return "Must be after the start. " + (_open_dates_constraint(event) or "")


def _archived_lock(message):
    """The lock the endpoint itself enforces, with the message it answers with."""

    def lock(event):
        if event.status == EventStatus.ARCHIVED:
            return Lock("event_archived", message)
        return None

    return lock


# The event endpoint and the configuration endpoints word the same refusal differently.
_ARCHIVED_EVENT = _archived_lock("Archived events cannot be edited.")
_ARCHIVED_CONFIG = _archived_lock("Archived event configuration cannot be edited.")


SPECS = [
    SettingSpec(
        "event.name",
        "core",
        BASE,
        "Name",
        "What the event is called.",
        {"type": "string", "minLength": 1, "maxLength": 200},
        lambda e: e.name,
        None,
        _w(_EVENT, "name"),
        organizer_owned=True,
    ),
    SettingSpec(
        "event.description",
        "core",
        BASE,
        "Description",
        "A short description of the event.",
        {"type": "string"},
        lambda e: e.description,
        "",
        _w(_EVENT, "description"),
    ),
    SettingSpec(
        "event.timezone",
        "core",
        BASE,
        "Time zone",
        "The zone the organizer schedules in; deadlines and the end date keep its wall clock.",
        {"type": "string", "description": "IANA time zone name"},
        lambda e: e.timezone,
        "UTC",
        _w(_EVENT, "timezone"),
        organizer_owned=True,
    ),
    SettingSpec(
        "event.starts_at",
        "core",
        BASE,
        "Start",
        "When the event begins.",
        {"type": ["string", "null"], "format": "date-time"},
        lambda e: _iso(e.starts_at),
        None,
        _w(_EVENT, "starts_at"),
        organizer_owned=True,
        constraint=_starts_constraint,
    ),
    SettingSpec(
        "event.ends_at",
        "core",
        BASE,
        "End",
        "When the event ends.",
        {"type": ["string", "null"], "format": "date-time"},
        lambda e: _iso(e.ends_at),
        None,
        _w(_EVENT, "ends_at"),
        organizer_owned=True,
        constraint=_ends_constraint,
    ),
    SettingSpec(
        "event.is_public",
        "core",
        BASE,
        "Public",
        "Whether visitors can see the event page.",
        {"type": "boolean"},
        lambda e: e.is_public,
        False,
        _w(_EVENT, "is_public"),
    ),
    SettingSpec(
        "registration.mode",
        "core",
        BASE,
        "Registration",
        "How people join: open to anyone, by application, or by invite code.",
        {"type": "string", "enum": list(RegistrationMode.values)},
        lambda e: _registration(e).mode,
        RegistrationMode.OPEN,
        _w(_REGISTRATION, "mode"),
    ),
    SettingSpec(
        "registration.capacity",
        "core",
        ADVANCED,
        "Registration capacity",
        "The most participants that can be approved; empty means no limit.",
        {"type": ["integer", "null"], "minimum": 1},
        lambda e: _registration(e).capacity,
        None,
        _w(_REGISTRATION, "capacity"),
        constraint="At least 1; leave empty for no limit.",
    ),
    SettingSpec(
        "registration.waitlist_enabled",
        "core",
        ADVANCED,
        "Waitlist",
        "Queue approved applicants beyond the capacity instead of refusing them.",
        {"type": "boolean"},
        lambda e: _registration(e).waitlist_enabled,
        False,
        _w(_REGISTRATION, "waitlist_enabled"),
    ),
    SettingSpec(
        "team.min_size",
        "core",
        BASE,
        "Smallest team",
        "Fewest members a team may have.",
        {"type": ["integer", "null"], "minimum": 1, "maximum": 100},
        lambda e: _rules(e).min_team_size,
        None,
        _w(_RULES, "min_team_size"),
        constraint="Between 1 and 100, and not above the largest team.",
    ),
    SettingSpec(
        "team.max_size",
        "core",
        BASE,
        "Largest team",
        "Most members a team may have.",
        {"type": ["integer", "null"], "minimum": 1, "maximum": 100},
        lambda e: _rules(e).max_team_size,
        None,
        _w(_RULES, "max_team_size"),
        constraint="Between 1 and 100, and not below the smallest team.",
    ),
    SettingSpec(
        "submission.required_artifact_kinds",
        "core",
        BASE,
        "Required evidence",
        "The kinds of evidence every project must attach.",
        {
            "type": "array",
            "items": {"type": "string", "enum": list(ArtifactKind.values)},
            "uniqueItems": True,
        },
        lambda e: list(_rules(e).required_artifact_kinds or []),
        [],
        _w(_RULES, "required_artifact_kinds"),
        constraint="Each kind at most once, from the known evidence kinds.",
    ),
    SettingSpec(
        "submission.require_finalized",
        "core",
        ADVANCED,
        "Require a final submission",
        "A project is only eligible once its submission is finalized.",
        {"type": "boolean"},
        lambda e: _rules(e).require_finalized_submission,
        False,
        _w(_RULES, "require_finalized_submission"),
    ),
    SettingSpec(
        "eligibility.require_track",
        "core",
        ADVANCED,
        "Require a track",
        "Every project must pick one of the event's tracks.",
        {"type": "boolean"},
        lambda e: _rules(e).require_track,
        False,
        _w(_RULES, "require_track"),
    ),
    SettingSpec(
        "eligibility.require_clearance",
        "eligibility_review",
        ADVANCED,
        "Require clearance",
        "A project must be cleared in eligibility review before it can advance.",
        {"type": "boolean"},
        lambda e: _rules(e).require_clearance,
        False,
        _w(_RULES, "require_clearance"),
    ),
    SettingSpec(
        "dates.duration_hours",
        "core",
        BASE,
        "Duration",
        "Hours between the start and the end; derived from the two dates.",
        {"type": ["number", "null"]},
        _duration_hours,
        None,
        None,
        derived=True,
    ),
]
for _spec in SPECS:
    if _spec.lock is None and not _spec.derived:
        object.__setattr__(
            _spec,
            "lock",
            _ARCHIVED_EVENT if _spec.write.path.endswith("{event}/") else _ARCHIVED_CONFIG,
        )

BY_KEY = {spec.key: spec for spec in SPECS}
assert len(BY_KEY) == len(SPECS), "duplicate setting key"
