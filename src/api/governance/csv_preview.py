"""Read-only preview of a project CSV against an event: suggests a column mapping and
reports, per row, exactly what would be refused (unknown owner, unknown track, blank
name, duplicate name) before anything is imported."""

import csv
import io
import re

from django.core.exceptions import ValidationError
from events.models import Track
from workspaces.models import Membership

MAX_BYTES = 1_000_000
MAX_ROWS = 2000
SAMPLE = 5
FIELDS = ("name", "created_by_username", "description", "track", "external_id")
REQUIRED = ("name", "created_by_username")
_ALIASES = {
    "name": {"name", "title", "project", "projectname", "projecttitle"},
    "created_by_username": {
        "owner",
        "username",
        "user",
        "leader",
        "author",
        "createdby",
        "creator",
    },
    "description": {"description", "summary", "pitch", "about", "tagline"},
    "track": {"track", "category", "theme"},
    "external_id": {"id", "externalid", "ref", "reference", "submissionid"},
}


def _norm(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def suggest_mapping(headers):
    mapping, used = {}, set()
    for field in FIELDS:
        for header in headers:
            if header not in used and _norm(header) in _ALIASES[field]:
                mapping[field] = header
                used.add(header)
                break
    return mapping


def preview(event, csv_text, mapping=None):
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValidationError("csv_text is required.")
    if len(csv_text.encode()) > MAX_BYTES:
        raise ValidationError("CSV is larger than 1 MB.")
    try:
        reader = csv.DictReader(io.StringIO(csv_text.lstrip("﻿")))
        headers = [h for h in (reader.fieldnames or []) if h]
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) > MAX_ROWS:
                raise ValidationError(f"CSV has more than {MAX_ROWS} rows.")
    except csv.Error as exc:
        raise ValidationError(f"CSV could not be read: {exc}") from exc
    if not headers:
        raise ValidationError("CSV needs a header row.")
    if len(set(headers)) != len(headers):
        raise ValidationError("CSV header names must be unique.")
    suggested = suggest_mapping(headers)
    used = suggested if mapping is None else mapping
    if not isinstance(used, dict) or set(used) - set(FIELDS):
        raise ValidationError(f"mapping may only use: {', '.join(FIELDS)}.")
    if any(value not in headers for value in used.values()):
        raise ValidationError("mapping refers to a column that is not in the CSV.")
    if len(set(used.values())) != len(used):
        raise ValidationError("Each mapped field needs its own CSV column.")
    missing = [field for field in REQUIRED if field not in used]

    members = set(
        Membership.objects.filter(workspace=event.workspace).values_list(
            "user__username", flat=True
        )
    )
    tracks = {t.name.casefold() for t in Track.objects.filter(event=event)}
    errors, sample, seen, ok = [], [], {}, 0
    if not missing:
        for number, row in enumerate(rows, start=2):
            problems = []
            name = (row.get(used["name"]) or "").strip()
            owner = (row.get(used["created_by_username"]) or "").strip()
            if not name:
                problems.append(("name", "Name is blank."))
            elif name.casefold() in seen:
                problems.append(("name", f"Duplicate of row {seen[name.casefold()]}."))
            else:
                seen[name.casefold()] = number
            if not owner:
                problems.append(("created_by_username", "Owner is blank."))
            elif owner not in members:
                problems.append(("created_by_username", f"{owner!r} is not in this workspace."))
            track = (row.get(used["track"]) or "").strip() if "track" in used else ""
            if track and track.casefold() not in tracks:
                problems.append(("track", f"Unknown track {track!r}."))
            for field, message in problems:
                errors.append({"row": number, "field": field, "message": message})
            if not problems:
                ok += 1
            if len(sample) < SAMPLE:
                sample.append(
                    {"row": number, **{f: (row.get(c) or "").strip() for f, c in used.items()}}
                )
    return {
        "headers": headers,
        "suggested_mapping": suggested,
        "mapping": used,
        "missing_required": missing,
        "rows": len(rows),
        "importable_rows": ok,
        "errors": errors[:100],
        "error_count": len(errors),
        "sample": sample,
    }
