"""Comparing two versions of the same thing, as one primitive (VERSION_DIFF, PD-F002-B02-T05).

Anything that keeps versions (form versions, rubric versions, a configuration change) shows what
changed the same way: a structural diff of JSON or a line diff of text, produced here and drawn by
the browser, never computed there.

    version_diff.diff_json(before, after)  # {"kind": "json", "changes": [{path, op, ...}], ...}
    version_diff.diff_text(before, after)  # {"kind": "text", "hunks": [...], "added": n, ...}
    version_diff.register_source(
        VersionSource("form", "Form", ("event", "form"), versions, snapshot))

Rules
- Pure and deterministic: the same two values always give the same answer, in the same order. A
  diff reads two snapshots; it never decides, restores or changes anything. Restoring stays the
  owning domain's own endpoint.
- Paths are JSON Pointers (RFC 6901, `/fields/2/label`; `~` and `/` escaped), `""` for the value
  itself. Ops are `added`, `removed`, `changed` and (keyed lists only) `moved`.
- A list whose items are all objects with a unique `id`, `key` or `public_id` (in both versions)
  is compared by that identity, so inserting or reordering an item does not make every item after
  it look changed. Other lists are compared by position.
- Bounded: at most 500 changes (`total` still counts them all), values over 1,000 characters are
  clipped (`clipped: true`), nesting beyond 24 levels is compared as one value, and text beyond
  5,000 lines or 200,000 characters is refused (`DiffError`, code `too_large`).
- A source owns visibility: `versions` and `snapshot` return None for what the caller may not see,
  and the endpoint answers 404.
"""

import difflib
import json
from collections.abc import Callable
from dataclasses import dataclass

MAX_CHANGES = 500
MAX_DEPTH = 24
MAX_VALUE_CHARS = 1000
MAX_LINES = 5000
MAX_TEXT_CHARS = 200_000
MAX_LINE_CHARS = 500
MAX_HUNK_LINES = 2000
CONTEXT = 3
INLINE_TEXT = 120  # a string longer than this, or with a line break, is compared as text
IDENTITY_KEYS = ("id", "key", "public_id")


class DiffError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def pointer(*parts) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def _same(a, b) -> bool:
    """Equality for JSON values in which `true` is not `1`."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, dict) or isinstance(b, dict):
        return (
            isinstance(a, dict)
            and isinstance(b, dict)
            and a.keys() == b.keys()
            and all(_same(a[k], b[k]) for k in a)
        )
    if isinstance(a, list) or isinstance(b, list):
        return (
            isinstance(a, list)
            and isinstance(b, list)
            and len(a) == len(b)
            and all(_same(x, y) for x, y in zip(a, b, strict=True))
        )
    if isinstance(a, int | float) and isinstance(b, int | float):
        return a == b
    return type(a) is type(b) and a == b


def _unmoved(ranks: list[int]) -> set[int]:
    """Positions in the longest increasing run of `ranks`: those items kept their relative order,
    so only the others count as moved (one item taken to the front is one move, not all)."""
    tails: list[int] = []  # index in `ranks` of the smallest tail of a run of each length
    back = [-1] * len(ranks)
    for position, rank in enumerate(ranks):
        low, high = 0, len(tails)
        while low < high:
            mid = (low + high) // 2
            if ranks[tails[mid]] < rank:
                low = mid + 1
            else:
                high = mid
        if low:
            back[position] = tails[low - 1]
        if low == len(tails):
            tails.append(position)
        else:
            tails[low] = position
    keep: set[int] = set()
    position = tails[-1] if tails else -1
    while position != -1:
        keep.add(position)
        position = back[position]
    return keep


def _clip(value):
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    if len(text) <= MAX_VALUE_CHARS:
        return value, False
    return text[: MAX_VALUE_CHARS - 1] + "…", True


def _identity(before: list, after: list) -> str | None:
    for key in IDENTITY_KEYS:
        seen = []
        for items in (before, after):
            values = []
            for item in items:
                value = item.get(key) if isinstance(item, dict) else None
                if not isinstance(value, str | int) or isinstance(value, bool):
                    break
                values.append(value)
            else:
                if len(set(values)) == len(values):
                    seen.append(values)
                    continue
            break
        if len(seen) == 2:
            return key
    return None


class _Changes:
    def __init__(self):
        self.rows: list[dict] = []
        self.total = 0

    def add(self, path, op, before=None, after=None):
        self.total += 1
        if len(self.rows) >= MAX_CHANGES:
            return
        row = {"path": path, "op": op, "before": None, "after": None, "clipped": False}
        clipped = False
        if op in ("removed", "changed"):
            row["before"], flag = _clip(before)
            clipped = clipped or flag
        elif op == "moved":
            row["before"] = before
        if op in ("added", "changed"):
            row["after"], flag = _clip(after)
            clipped = clipped or flag
        elif op == "moved":
            row["after"] = after
        row["clipped"] = clipped
        self.rows.append(row)


def _walk(out: _Changes, a, b, path: tuple, depth: int) -> None:
    if _same(a, b):
        return
    if depth < MAX_DEPTH and isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(a.keys() | b.keys(), key=str):
            here = (*path, key)
            if key not in b:
                out.add(pointer(*here), "removed", before=a[key])
            elif key not in a:
                out.add(pointer(*here), "added", after=b[key])
            else:
                _walk(out, a[key], b[key], here, depth + 1)
    elif depth < MAX_DEPTH and isinstance(a, list) and isinstance(b, list):
        key = _identity(a, b)
        if key is None:
            for index in range(max(len(a), len(b))):
                here = (*path, index)
                if index >= len(b):
                    out.add(pointer(*here), "removed", before=a[index])
                elif index >= len(a):
                    out.add(pointer(*here), "added", after=b[index])
                else:
                    _walk(out, a[index], b[index], here, depth + 1)
            return
        old = {item[key]: index for index, item in enumerate(a)}
        new = {item[key]: index for index, item in enumerate(b)}
        for identity, index in old.items():
            if identity not in new:
                out.add(pointer(*path, index), "removed", before=a[index])
        common = [identity for identity in new if identity in old]
        kept = _unmoved([old[identity] for identity in common])
        shifted = {identity for rank, identity in enumerate(common) if rank not in kept}
        for identity, index in new.items():
            here = (*path, index)
            if identity not in old:
                out.add(pointer(*here), "added", after=b[index])
                continue
            if identity in shifted:
                out.add(pointer(*here), "moved", before=old[identity], after=index)
            _walk(out, a[old[identity]], b[index], here, depth + 1)
    else:
        out.add(pointer(*path), "changed", before=a, after=b)


def diff_json(before, after) -> dict:
    """The structural changes from `before` to `after`, in a stable order."""
    out = _Changes()
    _walk(out, before, after, (), 0)
    return {
        "kind": "json",
        "changes": out.rows,
        "total": out.total,
        "truncated": out.total > len(out.rows),
    }


def _lines(text: str, which: str) -> list[str]:
    if len(text) > MAX_TEXT_CHARS:
        raise DiffError(
            "too_large", f"The {which} text is longer than {MAX_TEXT_CHARS:,} characters."
        )
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) > MAX_LINES:
        raise DiffError("too_large", f"The {which} text has more than {MAX_LINES:,} lines.")
    return lines


def diff_text(before: str, after: str) -> dict:
    """A line diff as hunks with three lines of context, in file order."""
    a, b = _lines(before or "", "before"), _lines(after or "", "after")
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    added = removed = shown = 0
    hunks, truncated = [], False
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed += i2 - i1
        if tag in ("replace", "insert"):
            added += j2 - j1
    for group in matcher.get_grouped_opcodes(CONTEXT):
        lines = []
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                lines += [("equal", a[i], i + 1, j1 + k + 1) for k, i in enumerate(range(i1, i2))]
                continue
            lines += (
                [("remove", a[i], i + 1, None) for i in range(i1, i2)] if tag != "insert" else []
            )
            lines += [("add", b[j], None, j + 1) for j in range(j1, j2)] if tag != "delete" else []
        if shown + len(lines) > MAX_HUNK_LINES:
            lines, truncated = lines[: max(0, MAX_HUNK_LINES - shown)], True
        shown += len(lines)
        hunks.append(
            {
                "lines": [
                    {
                        "op": op,
                        "text": text[:MAX_LINE_CHARS],
                        "before_line": old,
                        "after_line": new,
                    }
                    for op, text, old, new in lines
                ]
            }
        )
        if truncated:
            break
    return {
        "kind": "text",
        "hunks": [h for h in hunks if h["lines"]],
        "added": added,
        "removed": removed,
        "truncated": truncated,
    }


def diff_value(before, after) -> dict:
    """One changed value as the right kind of diff: text for prose, structure for the rest."""
    if isinstance(before, str) and isinstance(after, str):
        if "\n" in before + after or max(len(before), len(after)) > INLINE_TEXT:
            try:
                return diff_text(before, after)
            except DiffError:
                pass  # too large to line-diff: shown as one clipped change below
    return diff_json(before, after)


# --- versioned resources ------------------------------------------------------------------


@dataclass(frozen=True)
class VersionInfo:
    id: str
    label: str
    at: str | None = None  # ISO time
    by: str | None = None
    current: bool = False  # the live draft or value rather than a kept version


@dataclass(frozen=True)
class VersionSource:
    """A resource that keeps versions. Both callables return None for what `user` may not see.

    `versions(user, workspace, ref) -> list[VersionInfo] | None`, oldest first;
    `snapshot(user, workspace, ref, version_id) -> (found, value)`.
    """

    key: str
    label: str
    params: tuple[str, ...]
    versions: Callable
    snapshot: Callable
    kind: str = "json"  # or "text": how snapshots are compared


SOURCES: dict[str, VersionSource] = {}


def register_source(source: VersionSource) -> None:
    if source.key in SOURCES and SOURCES[source.key] is not source:
        raise ValueError(f"Version source '{source.key}' is already registered.")
    SOURCES[source.key] = source


def versions_of(source_key: str, user, workspace, ref: dict):
    """The versions the caller may compare, or None when the resource is not theirs to see."""
    source = SOURCES.get(source_key)
    return None if source is None else source.versions(user, workspace, ref)


def compare(source_key: str, user, workspace, ref: dict, before_id: str, after_id: str):
    """The diff between two versions, or None when either is unknown or not visible."""
    source = SOURCES.get(source_key)
    listed = versions_of(source_key, user, workspace, ref)
    if source is None or listed is None:
        return None
    by_id = {v.id: v for v in listed}
    if before_id not in by_id or after_id not in by_id:
        return None
    found_a, first = source.snapshot(user, workspace, ref, before_id)
    found_b, second = source.snapshot(user, workspace, ref, after_id)
    if not (found_a and found_b):
        return None
    diff = diff_text(first, second) if source.kind == "text" else diff_json(first, second)
    return {
        "source": source_key,
        "older": by_id[before_id],
        "newer": by_id[after_id],
        "diff": diff,
    }
