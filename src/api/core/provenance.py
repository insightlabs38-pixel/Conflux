"""What a derived or exported result was made from, by whom, under which rules (AUDIT_PROVENANCE,
PD-F002-B02-T07).

An audit row says *that* something happened; a provenance **envelope** says what the result was
built from, so a person can trace it later. It lives where results already live, in
`AuditEvent.metadata["provenance"]` and in a job's result, with no new table and no new endpoint:

    metadata = provenance.attach({"event_id": ...}, provenance.envelope(
        by=actor, source_kind="config_history", source_id=row.public_id,
        summary="Restored 2 fields.", refs=[{"kind": "audit_event", "id": row.public_id}],
        rules=("restore_before_values", 1), changes=provenance.changes_of(diff)))
    record_mutation(..., metadata=metadata)

    {"version": 1, "by": {"public_id", "username"} | None, "at": "2026-10-01T10:00:00Z",
     "source": {"kind", "id"},
     "inputs": {"digest": "<sha256>" | None, "refs": [{kind, id, label?}]},
     "rules": {"name", "version"} | None,
     "output": {"name", "bytes", "sha256"} | None,
     "summary": "One sentence.",
     "changes": {"total", "added", "removed", "changed", "moved"} | None}

Rules
- An envelope states what was used and by whom. It adds **no signature layer**: nothing here proves
  who wrote the audit row, and it never claims to.
- A digest is kept only where someone must be able to check a result later. `inputs.digest` is the
  SHA-256 of the canonical JSON of the `inputs` value when the caller passes one; `output` carries
  the SHA-256 of a downloaded file so it can be compared offline (`sha256sum file`) or in the
  browser. Everything else is references (`refs`), which are cheap and sufficient to trace.
- Canonical JSON is sorted keys, compact separators, UTF-8, no NaN: the same value always has the
  same digest on any machine.
- Bounded: summary 300 characters, 20 references, labels 120. Every string is data for a text node.
- No secrets, no content: references name things by kind and id (and a label), never their text.
"""

import hashlib
import json
from datetime import datetime

from django.utils import timezone

VERSION = 1
MAX_SUMMARY = 300
MAX_REFS = 20
MAX_LABEL = 120


def canonical(value) -> bytes:
    """The one byte form of a JSON value that digests are taken over."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _text(value, limit) -> str:
    text = "".join(ch if ch.isprintable() else "�" for ch in str(value))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _iso(value) -> str:
    value = value or timezone.now()
    return value.isoformat().replace("+00:00", "Z") if isinstance(value, datetime) else str(value)


def _ref(item) -> dict:
    row = {"kind": _text(item["kind"], 60), "id": _text(item["id"], 80)}
    if item.get("label"):
        row["label"] = _text(item["label"], MAX_LABEL)
    return row


def describe_output(name: str, data: bytes) -> dict:
    """The checkable facts of a file someone will download."""
    return {
        "name": _text(name, 200),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def changes_of(diff: dict | None) -> dict | None:
    """A count of what a `core.version_diff` JSON diff changed, for the envelope's summary."""
    if not diff or diff.get("kind") != "json":
        return None
    counts = {"added": 0, "removed": 0, "changed": 0, "moved": 0}
    for change in diff["changes"]:
        counts[change["op"]] += 1
    return {"total": diff["total"], **counts}


def envelope(
    *,
    by,
    source_kind: str,
    source_id,
    summary: str,
    refs=(),
    inputs=None,
    rules=None,
    output: dict | None = None,
    changes: dict | None = None,
    at=None,
) -> dict:
    """One provenance envelope. `by` is a user (or None for the system); `rules` is a
    `(name, version)` pair; `inputs`, when given, is a JSON value that will be digested."""
    refs = [_ref(r) for r in list(refs)[:MAX_REFS]]
    return {
        "version": VERSION,
        "by": {"public_id": str(by.public_id), "username": by.username}
        if by is not None and getattr(by, "is_authenticated", True)
        else None,
        "at": _iso(at),
        "source": {"kind": _text(source_kind, 60), "id": _text(source_id, 80)},
        "inputs": {"digest": digest(inputs) if inputs is not None else None, "refs": refs},
        "rules": {"name": _text(rules[0], 80), "version": rules[1]} if rules else None,
        "output": dict(output) if output else None,
        "summary": _text(summary, MAX_SUMMARY),
        "changes": dict(changes) if changes else None,
    }


def attach(metadata: dict | None, provenance: dict) -> dict:
    """`metadata` with the envelope under `provenance` (the audit row's one place for it)."""
    return {**(metadata or {}), "provenance": provenance}


def verify_output(provenance: dict, data: bytes) -> bool:
    """Is `data` the file this envelope describes? Offline: needs only the bytes and the record."""
    output = (provenance or {}).get("output")
    return bool(output) and output.get("sha256") == hashlib.sha256(data).hexdigest()


def problems(provenance) -> list[str]:
    """What is wrong with an envelope read back from storage (empty when it is well formed)."""
    if not isinstance(provenance, dict):
        return ["Not an object."]
    found = []
    for key in ("version", "by", "at", "source", "inputs", "rules", "output", "summary", "changes"):
        if key not in provenance:
            found.append(f"Missing {key}.")
    source = provenance.get("source")
    if not (isinstance(source, dict) and source.get("kind") and source.get("id")):
        found.append("The source needs a kind and an id.")
    inputs = provenance.get("inputs")
    if not (isinstance(inputs, dict) and isinstance(inputs.get("refs"), list)):
        found.append("The inputs need a list of references.")
    output = provenance.get("output")
    if output is not None and not (
        isinstance(output, dict) and len(str(output.get("sha256", ""))) == 64
    ):
        found.append("An output needs a SHA-256.")
    return found
