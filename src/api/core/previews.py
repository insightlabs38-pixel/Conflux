"""Safe previews of files and links as one primitive (ARTIFACT_PREVIEW, PD-F002-B02-T03).

A feature that holds a file or a link registers a **source**: how to find the thing for a caller
and what is already known about it. The pipeline turns that into one **descriptor** the browser
draws the same way everywhere (submitted evidence, a job's output, whatever comes next):

    previews.register_source(previews.PreviewSource(
        "job_output", "Job output", params=("job", "name"), resolve=find_output))

Rules
- A descriptor is derived on every read and never stored. Nothing is rendered, executed, unpacked
  or fetched here: the pipeline only reshapes an inspection the source hands it (static facts,
  findings, a bounded text excerpt, an archive listing). Every string in it is data for a text node.
- Visibility is the source's own rule: `resolve` returns None for what the caller may not see, and
  the endpoint answers 404, so nothing leaks by guessing ids.
- Content that can run (web pages, SVG, programs), anything that failed a safety check and
  anything the source refuses (purged, too large) is `unavailable` with a reason, and gets no
  download. A file nobody recognises is `unavailable` too, with the download left in place.
- Media (images, video, documents, archives) is never inlined by the platform: `media` carries
  the source's existing attachment-only download address.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

KINDS = ("text", "image", "video", "document", "archive", "data", "link", "unavailable")
STATES = ("ready", "pending", "unavailable")
LEVELS = ("info", "warning", "blocked")

MAX_FINDINGS = 20
MAX_ENTRIES = 50
MAX_TEXT = 4000
MAX_FACTS = 30
MAX_FACT_TEXT = 300
_DATA_SUFFIXES = (".csv", ".tsv", ".json", ".jsonl", ".ndjson")
_BY_DETECTED = {
    "png": "image",
    "jpeg": "image",
    "gif": "image",
    "webp": "image",
    "mp4": "video",
    "pdf": "document",
    "zip": "archive",
    "gzip": "archive",
}
_WITHHELD = {"html", "svg", "executable"}  # content that can run: never previewed


@dataclass
class Subject:
    """What a source knows about one thing, in the shape of a static inspection."""

    name: str
    content_type: str = ""
    size: int | None = None
    kind_hint: str = ""  # the feature's own word for it (an artifact's kind), used for datasets
    external_url: str = ""
    download_url: str | None = None  # the source's own attachment-only address
    inspection: dict | None = None  # verdict, detected_type, subject, findings, facts, preview
    unavailable: tuple[str, str] | None = None  # (code, message) when the source refuses


@dataclass(frozen=True)
class PreviewSource:
    key: str
    label: str
    params: tuple[str, ...]
    resolve: Callable  # (user, workspace, {param: value}) -> Subject | None


SOURCES: dict[str, PreviewSource] = {}


def register_source(source: PreviewSource) -> None:
    if source.key in SOURCES and SOURCES[source.key] is not source:
        raise ValueError(f"Preview source '{source.key}' is already registered.")
    SOURCES[source.key] = source


def _safe_link(url: str) -> bool:
    return url.lower().startswith(("http://", "https://"))


def _text(value, limit=MAX_FACT_TEXT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = "".join(ch if ch.isprintable() else "�" for ch in text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _facts(raw: dict) -> dict:
    facts = {}
    for key, value in raw.items():
        if key == "listing" or len(facts) >= MAX_FACTS:
            continue
        facts[_text(key, 60)] = value if isinstance(value, bool | int | float) else _text(value)
    return facts


def _findings(raw: list) -> tuple[list[dict], int]:
    rows = []
    for item in raw[:MAX_FINDINGS]:
        level = item.get("severity")
        rows.append(
            {
                "level": level if level in LEVELS else "info",
                "code": _text(item.get("code", ""), 60),
                "message": _text(item.get("detail") or item.get("code") or "", 500),
            }
        )
    return rows, len(raw)


def _kind(subject: Subject, inspection: dict) -> str:
    if inspection.get("subject") == "link":
        return "link"
    detected = inspection.get("detected_type", "")
    if detected == "text":
        name = subject.name.lower()
        if subject.kind_hint == "dataset" or name.endswith(_DATA_SUFFIXES):
            return "data"
        return "text"
    return _BY_DETECTED.get(detected, "unavailable")


def _iso(value) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return value or None


def descriptor(source: str, ref: dict, subject: Subject) -> dict:
    """The one shape the browser draws. Pure: the same subject always gives the same answer."""
    base = {
        "source": source,
        "ref": ref,
        "name": _text(subject.name, 200),
        "content_type": _text(subject.content_type, 100),
        "size": subject.size,
        "kind": "unavailable",
        "detected_type": "",
        "state": "unavailable",
        "reason": None,
        "facts": {},
        "findings": [],
        "findings_total": 0,
        "text": "",
        "entries": [],
        "entries_total": 0,
        "media": None,
        "link": None,
        "inspected_at": None,
    }
    if subject.unavailable:
        base["reason"] = {"code": subject.unavailable[0], "message": subject.unavailable[1]}
        return base
    inspection = subject.inspection
    link = subject.external_url if _safe_link(subject.external_url) else None
    if inspection is None:
        base["state"] = "pending"
        base["reason"] = {
            "code": "not_inspected",
            "message": "This has not been inspected yet; run the safe inspection to preview it.",
        }
        if subject.external_url:
            base["kind"], base["link"] = ("link", link)
        elif subject.download_url:
            base["media"] = {"url": subject.download_url, "filename": _text(subject.name, 200)}
        return base
    base["findings"], base["findings_total"] = _findings(inspection.get("findings") or [])
    base["facts"] = _facts(inspection.get("facts") or {})
    base["inspected_at"] = _iso(inspection.get("inspected_at"))
    detected = inspection.get("detected_type", "")
    base["detected_type"] = _text(detected, 40)
    blocked = inspection.get("verdict") == "blocked" or detected in _WITHHELD
    if blocked:
        first = next((f for f in base["findings"] if f["level"] == "blocked"), None)
        base["reason"] = {
            "code": first["code"] if first else "withheld",
            "message": "Withheld from preview: "
            + (first["message"] if first else "the content can run or failed a safety check."),
        }
        return base
    kind = _kind(subject, inspection)
    base["kind"] = kind
    if kind == "link":
        base["link"] = link
        base["state"] = "ready" if link else "unavailable"
        if not link:
            base["reason"] = {"code": "unsafe_link", "message": "Only web links are shown."}
        return base
    if subject.download_url:
        base["media"] = {"url": subject.download_url, "filename": _text(subject.name, 200)}
    if kind == "unavailable":
        base["reason"] = {
            "code": "no_preview",
            "message": "There is no preview for this kind of file; download it to open it.",
        }
        return base
    base["state"] = "ready"
    if kind in ("text", "data"):
        base["text"] = (inspection.get("preview") or "")[:MAX_TEXT]
    if kind == "archive":
        listing = (inspection.get("facts") or {}).get("listing") or []
        base["entries"] = [
            {"name": _text(entry.get("name", ""), 200), "size": entry.get("size")}
            for entry in listing[:MAX_ENTRIES]
            if isinstance(entry, dict)
        ]
        total = (inspection.get("facts") or {}).get("entries")
        base["entries_total"] = total if isinstance(total, int) else len(base["entries"])
    return base


def describe(source_key: str, user, workspace, ref: dict) -> dict | None:
    """The descriptor for `ref` as `user` may see it, or None when it is not theirs to see."""
    source = SOURCES.get(source_key)
    if source is None:
        return None
    subject = source.resolve(user, workspace, ref)
    return None if subject is None else descriptor(source_key, ref, subject)
