"""The event timeline: one derived, ordered view of everything time-boxed (PD-F002-B01-T08).

Nothing here is stored. Each domain registers a **provider** that reads its own rows and yields
`TimelineItem`s; the timeline merges, orders and checks them, and says for every item which
existing domain write changes its times. A time is never edited here: `item.write` names the
domain endpoint (the same descriptor shape the configuration registry uses) and that endpoint keeps
its own validation, audit and versioning.

Conflicts are **advisory facts, never blocks**, and fully deterministic (no clock, no heuristics):
- `window_inverted`: an item that ends at or before it starts;
- `<axis>_overlap` (`location`, `track`, `mentor`, ...): two items on the same exclusive resource
  overlap in time (an item names its resources in `group`);
- `outside_event`: an item flagged `inside_event` lies outside the event's own window;
- plus whatever a domain registers with `register_rule` (e.g. publication before voting closes).

Instants are real UTC instants. Each item also carries its rendering in the event's time zone and
a note when a window crosses a daylight-saving change.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

MAX_ITEMS = 500


@dataclass(frozen=True)
class Write:
    """The existing endpoint that changes an item's times (path relative to /api/v1/, with
    `{workspace}` and `{event}`). `fields` maps `starts_at`/`ends_at` to the body field each is
    sent as; `extra` are constant body fields the endpoint needs alongside the times (e.g. the
    stage a finalists schedule points at). The request body is the changed fields plus `extra`;
    an endpoint that replaces every input is described by putting what it needs in `extra`."""

    method: str
    path: str
    fields: dict
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TimelineItem:
    """One thing on the timeline. `ends_at` is None for an instant. `key` is stable and unique in
    the event (`<kind>:<id>`); `group` maps an axis (`location`, `track`, ...) to the exclusive
    resource the item occupies."""

    kind: str
    key: str
    label: str
    starts_at: datetime
    ends_at: datetime | None = None
    source: dict = field(default_factory=dict)
    group: dict = field(default_factory=dict)
    editable: bool = False
    write: Write | None = None
    inside_event: bool = False
    note: str = ""


@dataclass(frozen=True)
class Provider:
    """`items(event)` yields the TimelineItems of one kind; `label` names the kind for people."""

    key: str
    label: str
    items: Callable


@dataclass(frozen=True)
class Conflict:
    code: str
    message: str
    items: tuple


PROVIDERS: dict[str, Provider] = {}
RULES: list[Callable] = []


def register_provider(provider: Provider):
    """Add a provider once; a different registration under a taken key is a bug."""
    if provider.key in PROVIDERS and PROVIDERS[provider.key] != provider:
        raise ValueError(f"Timeline provider {provider.key!r} is already registered")
    PROVIDERS[provider.key] = provider
    return provider


def register_rule(rule: Callable):
    """`rule(event, items) -> list[Conflict]` over the full, unfiltered list of items."""
    if rule not in RULES:
        RULES.append(rule)
    return rule


def _end(item):
    return item.ends_at or item.starts_at


def _overlap(a, b):
    """Two real windows overlap when each starts before the other ends (touching is fine);
    an instant overlaps a window only if it falls strictly inside it."""
    if a.ends_at is None and b.ends_at is None:
        return a.starts_at == b.starts_at
    return a.starts_at < _end(b) and b.starts_at < _end(a)


def _inverted(event, items):
    return [
        Conflict(
            "window_inverted",
            f"{item.label} ends before it starts.",
            (item.key,),
        )
        for item in items
        if item.ends_at is not None and item.ends_at <= item.starts_at
    ]


def _overlaps(event, items):
    found = []
    by_resource = {}
    for item in items:
        for axis, resource in item.group.items():
            by_resource.setdefault((axis, resource), []).append(item)
    for (axis, _), members in sorted(by_resource.items(), key=lambda kv: str(kv[0])):
        members = sorted(members, key=lambda i: (i.starts_at, i.key))
        for index, first in enumerate(members):
            for second in members[index + 1 :]:
                if second.starts_at >= _end(first) and second.starts_at != first.starts_at:
                    break  # sorted by start: nothing later can overlap `first`
                if _overlap(first, second):
                    found.append(
                        Conflict(
                            f"{axis}_overlap",
                            f"{first.label} and {second.label} overlap on the same {axis}.",
                            (first.key, second.key),
                        )
                    )
    return found


def _outside_event(event, items):
    if event.starts_at is None or event.ends_at is None:
        return []
    return [
        Conflict(
            "outside_event",
            f"{item.label} is outside the event's dates.",
            (item.key,),
        )
        for item in items
        if item.inside_event and (item.starts_at < event.starts_at or _end(item) > event.ends_at)
    ]


GENERIC_RULES = (_inverted, _overlaps, _outside_event)


def collect(event, kinds=None):
    """Every item of the event (optionally only some kinds), unordered limits not applied."""
    items = []
    for provider in PROVIDERS.values():
        if kinds is None or provider.key in kinds:
            items.extend(provider.items(event))
    return sorted(items, key=lambda i: (i.starts_at, i.kind, i.key))


def conflicts(event, items):
    found = []
    for rule in (*GENERIC_RULES, *RULES):
        found.extend(rule(event, items))
    return sorted(found, key=lambda c: (c.code, c.items))


def _local(value, zone):
    return value.astimezone(zone).isoformat() if value else None


def _iso(value):
    return value.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z") if value else None


def _dst_note(item, zone):
    if item.ends_at is None:
        return None
    start_offset = item.starts_at.astimezone(zone).utcoffset()
    end_offset = item.ends_at.astimezone(zone).utcoffset()
    if start_offset == end_offset:
        return None
    return "Crosses a daylight-saving change: its wall-clock span differs from its real length."


def describe_item(item, zone):
    return {
        "kind": item.kind,
        "kind_label": PROVIDERS[item.kind].label if item.kind in PROVIDERS else item.kind,
        "key": item.key,
        "label": item.label,
        "starts_at": _iso(item.starts_at),
        "ends_at": _iso(item.ends_at),
        "local_starts_at": _local(item.starts_at, zone),
        "local_ends_at": _local(item.ends_at, zone),
        "dst_note": _dst_note(item, zone),
        "source": item.source,
        "editable": item.editable,
        "write": (
            {
                "method": item.write.method,
                "path": item.write.path,
                "fields": item.write.fields,
                "extra": item.write.extra,
            }
            if item.write
            else None
        ),
        "note": item.note,
    }


def build(event, *, start=None, end=None, kinds=None, limit=200):
    """The timeline as served: items inside [start, end], conflicts among them, the event zone."""
    unknown = set(kinds or ()) - set(PROVIDERS)
    if unknown:
        raise ValueError(f"Unknown kinds: {', '.join(sorted(unknown))}")
    zone = ZoneInfo(event.timezone or "UTC")
    everything = collect(event)  # conflicts are judged on the whole event, then filtered
    wanted = [i for i in everything if kinds is None or i.kind in kinds]
    if start is not None:
        wanted = [i for i in wanted if _end(i) >= start]
    if end is not None:
        wanted = [i for i in wanted if i.starts_at <= end]
    shown = {i.key for i in wanted}
    relevant = [c for c in conflicts(event, everything) if shown & set(c.items)]
    total = len(wanted)
    return {
        "event": str(event.public_id),
        "timezone": str(zone),
        "total": total,
        "items": [describe_item(i, zone) for i in wanted[:limit]],
        "conflicts": [
            {"code": c.code, "severity": "advisory", "message": c.message, "items": list(c.items)}
            for c in relevant
        ],
    }
