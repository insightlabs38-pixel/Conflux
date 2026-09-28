"""Agenda helpers: stream embed policy, iCalendar output, public event state."""

import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

from django.conf import settings

_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_VIMEO_ID = re.compile(r"^\d{6,12}$")


def embed_url(stream_url):
    """An iframe-safe URL for a known video host, else None (render a link instead).

    Only YouTube (privacy-enhanced domain), Vimeo and hosts an operator adds to
    CONFLUX_EMBED_HOSTS are ever framed; nothing user-supplied is used verbatim
    unless its host is explicitly trusted.
    """
    if not stream_url:
        return None
    parts = urlsplit(stream_url)
    host = (parts.hostname or "").lower().removeprefix("www.")
    if host in ("youtube.com", "m.youtube.com"):
        video = parse_qs(parts.query).get("v", [""])[0]
        if parts.path.startswith("/embed/"):
            video = parts.path.split("/")[2] if len(parts.path.split("/")) > 2 else ""
        return _youtube(video)
    if host == "youtu.be":
        return _youtube(parts.path.lstrip("/"))
    if host in ("vimeo.com", "player.vimeo.com"):
        video = parts.path.rstrip("/").split("/")[-1]
        if _VIMEO_ID.match(video):
            return f"https://player.vimeo.com/video/{video}"
        return None
    trusted = {h.strip().lower() for h in getattr(settings, "EMBED_HOSTS", []) if h.strip()}
    return stream_url if host in trusted else None


def _youtube(video):
    return f"https://www.youtube-nocookie.com/embed/{video}" if _YOUTUBE_ID.match(video) else None


def _escape(value):
    value = "".join(c for c in str(value) if c in "\n\t" or ord(c) >= 32)
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line):
    """RFC 5545 line folding at 75 octets without splitting a UTF-8 sequence."""
    encoded = line.encode()
    if len(encoded) <= 75:
        return line
    chunks, current, size = [], "", 0
    for char in line:
        width = len(char.encode())
        if size + width > (75 if not chunks else 74):
            chunks.append(current)
            current, size = "", 0
        current += char
        size += width
    chunks.append(current)
    return "\r\n ".join(chunks)


def _stamp(value):
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def build_ics(event, sessions, host):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Conflux//Agenda//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(event.name)}",
    ]
    for session in sessions:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{session.public_id}@{host}",
            f"DTSTAMP:{_stamp(session.updated_at)}",
            f"DTSTART:{_stamp(session.starts_at)}",
            f"DTEND:{_stamp(session.ends_at)}",
            f"SUMMARY:{_escape(session.title)}",
        ]
        if session.description:
            lines.append(f"DESCRIPTION:{_escape(session.description)}")
        if session.location:
            lines.append(f"LOCATION:{_escape(session.location.name)}")
        if session.stream_url:
            lines.append(f"URL:{session.stream_url}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def event_phase(event, now=None):
    now = now or datetime.now(UTC)
    if event.status == "closed" or event.status == "archived":
        return "ended"
    if event.starts_at and now < event.starts_at:
        return "upcoming"
    if event.ends_at and now >= event.ends_at:
        return "ended"
    return "live"
