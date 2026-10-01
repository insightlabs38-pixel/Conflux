"""Previewing as a role, as of a time or at a kept version (PREVIEW_CONTEXT, PD-F002-B03-T01).

An organizer often needs to know what somebody else would see: a participant looking at a form, a
judge at a rubric, the public at a page, as it is now, as it was at a deadline or as it was in
version 2. This is one primitive for all of them, without anyone impersonating anyone.

A **context** is data: `{role, at, version}` inside one request body. It is not an identity, a
header, a cookie or a stored row, and no domain endpoint reads it. The caller stays the actor, so
their authorization still applies and a role preview can only show a subset of what they could
already read. A **surface** is code-owned and registered; it declares which roles it can be viewed
as, which version source (`core.version_diff`) it reads and, optionally, a `schema_subset` schema
for its input:

    preview_context.register_surface(preview_context.Surface(
        key="form", label="Application form", params=("event", "form"),
        roles=("participant", "judge", "organizer", "public"), version_source="form",
        resolve=resolve))

`resolve(user, workspace, ref, resolved, input) -> dict | None` turns the resolved role, version
and its snapshot into a payload; None means the caller may not see it. Everything else (parsing,
choosing the version by id or by time, naming what was resolved, the sentence the UI shows) is
here, so every surface behaves the same.

Reading only and deterministic: an explicit `at` or `version` gives the same answer while the stored
versions are unchanged, and the response names the version it resolved so a caller can pin it.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from . import schema_subset, version_diff

MIN_AT = datetime(2000, 1, 1, tzinfo=UTC)
MAX_AT = datetime(2100, 1, 1, tzinfo=UTC)
CONTEXT_KEYS = ("role", "at", "version")
MAX_INPUT_BYTES = 20_000


class PreviewError(Exception):
    """A request the caller can fix: `problems` is the 400 body, `{path: [messages]}`."""

    def __init__(self, problems: dict[str, list[str]]):
        super().__init__("; ".join(f"{k}: {', '.join(v)}" for k, v in problems.items()))
        self.problems = problems


class NotVisible(Exception):
    """What the caller may not see or that does not exist: a 404, never a hint which."""


@dataclass(frozen=True)
class Context:
    role: str | None = None
    at: datetime | None = None
    version: str | None = None


@dataclass(frozen=True)
class Resolved:
    """What a surface receives: the role, the one version chosen and its snapshot."""

    role: str | None
    at: datetime | None
    version: version_diff.VersionInfo | None
    value: Any
    live: bool


@dataclass(frozen=True)
class Surface:
    key: str
    label: str
    params: tuple[str, ...]
    resolve: Callable
    roles: tuple[str, ...] = ()
    version_source: str | None = None
    input_schema: dict | None = None
    live: Callable | None = None  # (versions) -> VersionInfo: the version nobody asked for


SURFACES: dict[str, Surface] = {}


def register_surface(surface: Surface) -> None:
    if surface.key in SURFACES and SURFACES[surface.key] is not surface:
        raise ValueError(f"Preview surface '{surface.key}' is already registered.")
    if surface.version_source is not None and surface.version_source not in version_diff.SOURCES:
        raise ValueError(f"Surface '{surface.key}' names an unregistered version source.")
    SURFACES[surface.key] = surface


def _instant(text: str) -> datetime | None:
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value.astimezone(UTC) if value.tzinfo else None


def parse(raw, surface: Surface) -> Context:
    """The context a request asked for, or `PreviewError` naming each part that is wrong."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise PreviewError({"context": ["Send the context as an object."]})
    problems: dict[str, list[str]] = {}
    for name in raw:
        if name not in CONTEXT_KEYS:
            problems[f"context.{name}"] = ["Unknown context key; use role, at or version."]
    role, at, version = raw.get("role"), raw.get("at"), raw.get("version")
    if role is not None:
        if not surface.roles:
            problems["context.role"] = ["This preview has no roles to view it as."]
        elif role not in surface.roles:
            problems["context.role"] = [f"Use one of: {', '.join(surface.roles)}."]
    moment = None
    if at is not None:
        moment = _instant(at) if isinstance(at, str) else None
        if surface.version_source is None:
            problems["context.at"] = ["This preview keeps no versions, so it has no time to view."]
        elif moment is None:
            problems["context.at"] = ["Use a date and time with an offset (2027-03-06T10:00:00Z)."]
        elif not MIN_AT <= moment < MAX_AT:
            problems["context.at"] = ["Use a time between the years 2000 and 2100."]
    if version is not None:
        if not isinstance(version, str) or not 0 < len(version) <= 100:
            problems["context.version"] = ["Send the version id as text."]
        elif surface.version_source is None:
            problems["context.version"] = ["This preview keeps no versions."]
        elif at is not None:
            problems["context.version"] = ["Choose a version or a time, not both."]
    if problems:
        raise PreviewError(problems)
    return Context(role=role, at=moment, version=version)


def _pick(surface: Surface, listed, context: Context):
    """The one version the context points at, and whether it is the live default."""
    if context.version is not None:
        found = next((v for v in listed if v.id == context.version), None)
        if found is None:
            raise PreviewError({"context.version": ["No such version."]})
        return found, False
    if context.at is not None:
        kept = [(v, _instant(v.at)) for v in listed if v.at]
        before = [(v, moment) for v, moment in kept if moment and moment <= context.at]
        if not before:
            first = min((m for _, m in kept if m), default=None)
            message = (
                "Nothing was kept yet at that time; the first version was kept "
                f"{first.isoformat().replace('+00:00', 'Z')}."
                if first
                else "No version has been kept yet."
            )
            raise PreviewError({"context.at": [message]})
        return max(before, key=lambda pair: pair[1])[0], False
    if surface.live is not None:
        return surface.live(listed), True
    kept = [v for v in listed if v.at]
    return (kept[-1] if kept else listed[-1]), True


def _check_input(surface: Surface, raw):
    if raw is None or raw == {}:
        return {} if surface.input_schema is None else _normalised(surface, {})
    if surface.input_schema is None:
        raise PreviewError({"input": ["This preview takes no input."]})
    return _normalised(surface, raw)


def _normalised(surface, raw):
    if len(repr(raw)) > MAX_INPUT_BYTES:
        raise PreviewError({"input": ["The input is too large."]})
    try:
        return schema_subset.normalize(surface.input_schema, raw)
    except schema_subset.SchemaError as error:
        errors = schema_subset.api_errors(error.problems)
        raise PreviewError(
            {("input" if k == "value" else f"input.{k}"): v for k, v in errors.items()}
        ) from error


def sentence(role, version, at, live) -> str:
    parts = []
    if role:
        parts.append(f"as {role}")
    if version is not None:
        parts.append(f"{version.label} (live)" if live else version.label)
    if at is not None:
        parts.append("as of " + at.strftime("%Y-%m-%d %H:%M UTC"))
    return f"Previewing {', '.join(parts) or 'the live view'}. Nothing is saved or sent."


@dataclass
class Preview:
    surface: Surface
    resolved: Resolved
    versions: list = field(default_factory=list)
    notices: list = field(default_factory=list)
    data: Any = None

    def as_dict(self) -> dict:
        r = self.resolved
        return {
            "surface": self.surface.key,
            "label": self.surface.label,
            "summary": sentence(r.role, r.version, r.at, r.live),
            "roles": list(self.surface.roles),
            "versions": [asdict(v) for v in self.versions],
            "resolved": {
                "role": r.role,
                "at": r.at.isoformat().replace("+00:00", "Z") if r.at else None,
                "version": asdict(r.version) if r.version else None,
                "live": r.live,
            },
            "notices": self.notices,
            "data": self.data,
        }


def preview(surface_key: str, user, workspace, ref: dict, context_raw=None, input_raw=None):
    """Resolve a preview. Raises `NotVisible` (404) or `PreviewError` (400)."""
    surface = SURFACES.get(surface_key)
    if surface is None:
        raise NotVisible()
    context = parse(context_raw, surface)
    values = _check_input(surface, input_raw)
    listed, version, value, live = [], None, None, True
    if surface.version_source is not None:
        source = version_diff.SOURCES[surface.version_source]
        listed = source.versions(user, workspace, ref)
        if listed is None:
            raise NotVisible()
        if not listed:
            raise NotVisible()
        version, live = _pick(surface, listed, context)
        found, value = source.snapshot(user, workspace, ref, version.id)
        if not found:
            raise NotVisible()
    notices = []
    if live and version is not None and version.current:
        notices.append(
            {"code": "unpublished", "message": "Nothing has been published yet; this is the draft."}
        )
    resolved = Resolved(role=context.role, at=context.at, version=version, value=value, live=live)
    data = surface.resolve(user, workspace, ref, resolved, values)
    if data is None:
        raise NotVisible()
    return Preview(surface, resolved, listed, notices, data)
