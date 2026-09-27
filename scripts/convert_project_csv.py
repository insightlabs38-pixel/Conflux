"""Convert a mapped project CSV into a canonical full event archive."""

import argparse
import csv
import io
import json
import uuid
from pathlib import Path

MAX_CSV_BYTES = 5_000_000
MAX_ROWS = 10_000
MAPPING_KEYS = {"name", "created_by_username", "description", "track", "external_id"}
REQUIRED_MAPPING = {"name", "created_by_username"}


class ConversionError(ValueError):
    pass


def convert(archive, csv_text, mapping):
    if not isinstance(archive, dict) or archive.get("format_version") != 1:
        raise ConversionError("Input must be a version 1 canonical archive.")
    if archive.get("mode") != "config" or "projects" in archive:
        raise ConversionError("Input must be a config archive without projects.")
    if not isinstance(archive.get("event"), dict):
        raise ConversionError("Archive is missing event configuration.")
    if (
        not isinstance(mapping, dict)
        or set(mapping) - MAPPING_KEYS
        or not REQUIRED_MAPPING <= set(mapping)
    ):
        raise ConversionError("Mapping needs name and created_by_username and only known keys.")
    if any(not isinstance(value, str) or not value for value in mapping.values()):
        raise ConversionError("Every mapping value must name a CSV column.")
    if len(set(mapping.values())) != len(mapping):
        raise ConversionError("Each mapped field needs its own CSV column.")

    tracks = {}
    for item in archive.get("tracks", []):
        name = item.get("name")
        ref = item.get("ref")
        if not name or not ref or name in tracks:
            raise ConversionError("Archive tracks need unique names and references.")
        tracks[name] = ref

    reader = csv.DictReader(io.StringIO(csv_text, newline=""), strict=True)
    headers = reader.fieldnames
    if not headers or len(headers) != len(set(headers)) or any(not name for name in headers):
        raise ConversionError("CSV needs a header with unique nonempty column names.")
    missing = set(mapping.values()) - set(headers)
    if missing:
        raise ConversionError(f"Mapped columns are missing: {', '.join(sorted(missing))}.")

    projects = []
    seen_ids = set()
    try:
        for line_number, row in enumerate(reader, start=2):
            if len(projects) >= MAX_ROWS:
                raise ConversionError(f"CSV exceeds {MAX_ROWS} project rows.")
            if None in row or any(value is None for value in row.values()):
                raise ConversionError(f"CSV row {line_number} has the wrong number of fields.")
            name = row[mapping["name"]].strip()
            creator = row[mapping["created_by_username"]].strip()
            if not name or not creator or len(name) > 200:
                raise ConversionError(f"CSV row {line_number} needs a name (max 200) and creator.")
            track_name = row[mapping["track"]].strip() if "track" in mapping else ""
            if track_name and track_name not in tracks:
                raise ConversionError(f"CSV row {line_number} has unknown track {track_name!r}.")
            external_id = row[mapping["external_id"]].strip() if "external_id" in mapping else ""
            if "external_id" in mapping and not external_id:
                raise ConversionError(f"CSV row {line_number} has an empty external ID.")
            identity = external_id or f"{line_number}:{name}:{creator}"
            if identity in seen_ids:
                raise ConversionError(f"CSV row {line_number} repeats external ID {identity!r}.")
            seen_ids.add(identity)
            projects.append(
                {
                    "ref": str(uuid.uuid5(uuid.NAMESPACE_URL, "conflux-csv-project:" + identity)),
                    "name": name,
                    "description": row[mapping["description"]].strip()
                    if "description" in mapping
                    else "",
                    "track_ref": tracks.get(track_name),
                    "created_by_username": creator,
                }
            )
    except csv.Error as exc:
        raise ConversionError(f"Malformed CSV: {exc}") from exc
    if not projects:
        raise ConversionError("CSV has no project rows.")
    return {**archive, "mode": "full", "projects": projects}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.csv.stat().st_size > MAX_CSV_BYTES:
        parser.error(f"CSV exceeds {MAX_CSV_BYTES} bytes.")
    try:
        archive = json.loads(args.archive.read_text(encoding="utf-8"))
        mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
        csv_text = args.csv.read_text(encoding="utf-8-sig")
        output = convert(archive, csv_text, mapping)
        with args.output.open("x", encoding="utf-8") as destination:
            json.dump(output, destination, indent=2, ensure_ascii=False)
            destination.write("\n")
    except (OSError, UnicodeError, json.JSONDecodeError, ConversionError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
