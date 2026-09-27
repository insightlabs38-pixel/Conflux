"""VS24: presentation-layer DST/timezone safeguards for `TemporalGate`
(and the event's own start/end window). `opens_at`/`closes_at` are always
real UTC instants -- see `TemporalGate`'s docstring -- so there is never
an "ambiguous local time" problem with the stored data itself; the risk
this guards against is purely presentational: a window whose local-time
span crosses a DST transition in the event's declared timezone looks like
it covers a different number of wall-clock hours than it actually does in
elapsed UTC time, which is exactly the kind of thing that quietly breaks
an organizer's mental model of "this closes 3 hours after it opens."
"""

from zoneinfo import ZoneInfo


def local_iso(instant, tz_name):
    """`instant` (a UTC-aware datetime) rendered in `tz_name`, ISO 8601
    with its UTC offset -- e.g. "2026-11-01T09:00:00-05:00".
    """
    if instant is None:
        return None
    return instant.astimezone(ZoneInfo(tz_name)).isoformat()


def _format_offset(delta):
    total_minutes = int(delta.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return f"{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def dst_warning(opens_at, closes_at, tz_name):
    """None, or a human-readable warning that this window's UTC offset in
    `tz_name` changes between `opens_at` and `closes_at` -- detected by
    comparing the zone's UTC offset at each endpoint: offsets only change
    at real zone transitions, so a difference means one occurred somewhere
    inside the window, regardless of the window's length.
    """
    if opens_at is None or closes_at is None:
        return None
    zone = ZoneInfo(tz_name)
    open_offset = opens_at.astimezone(zone).utcoffset()
    close_offset = closes_at.astimezone(zone).utcoffset()
    if open_offset == close_offset:
        return None
    return (
        f"This window crosses a daylight-saving change in {tz_name}: the "
        f"local UTC offset shifts from {_format_offset(open_offset)} to "
        f"{_format_offset(close_offset)} partway through, so its wall-clock "
        "span looks different from its actual elapsed time."
    )
