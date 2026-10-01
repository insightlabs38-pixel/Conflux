/**
 * The client half of version comparison (PD-F002-B02-T05). The server compares two versions and
 * returns the diff (`core/version_diff.py`); the browser only draws it, so what is shown is exactly
 * what the server computed. Restoring a version stays the owning feature's own action.
 */
export type Change = {
  /** A JSON Pointer ("/fields/2/label"); "" is the value itself. */
  path: string;
  op: "added" | "removed" | "changed" | "moved";
  before: unknown;
  after: unknown;
  /** The value was cut to fit and is shown as text. */
  clipped: boolean;
};

export type JsonDiff = {
  kind: "json";
  changes: Change[];
  total: number;
  truncated: boolean;
};

export type DiffLine = {
  op: "equal" | "add" | "remove";
  text: string;
  before_line: number | null;
  after_line: number | null;
};

export type TextDiff = {
  kind: "text";
  hunks: { lines: DiffLine[] }[];
  added: number;
  removed: number;
  truncated: boolean;
};

export type Diff = JsonDiff | TextDiff;

export type VersionInfo = {
  id: string;
  label: string;
  at: string | null;
  by: string | null;
  current: boolean;
};

export type VersionList = {
  source: string;
  label: string;
  versions: VersionInfo[];
};

export type VersionComparison = {
  source: string;
  older: VersionInfo;
  newer: VersionInfo;
  diff: Diff;
};

const query = (
  reference: Record<string, string>,
  more: Record<string, string> = {},
) => new URLSearchParams({ ...reference, ...more }).toString();

export const versionsUrl = (
  workspaceId: string,
  source: string,
  reference: Record<string, string>,
) =>
  `/api/v1/workspaces/${workspaceId}/versions/${source}/?${query(reference)}`;

export const comparisonUrl = (
  workspaceId: string,
  source: string,
  reference: Record<string, string>,
  older: string,
  newer: string,
) =>
  `/api/v1/workspaces/${workspaceId}/versions/${source}/diff/?${query(reference, { older, newer })}`;

/** "/fields/2/label" -> "fields › 2 › label"; the value itself is "(whole value)". */
export function pathLabel(pointer: string): string {
  if (pointer === "") return "(whole value)";
  return pointer
    .slice(1)
    .split("/")
    .map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"))
    .join(" › ");
}

/** A value as one line of text for a change (strings keep their quotes so "1" and 1 differ). */
export const valueText = (value: unknown): string =>
  JSON.stringify(value) ?? "undefined";

/** How many changes a diff holds, in words. */
export function summary(diff: Diff): string {
  if (diff.kind === "json") {
    if (diff.total === 0) return "No differences.";
    const shown = diff.changes.length;
    const noun = diff.total === 1 ? "change" : "changes";
    return diff.truncated
      ? `Showing ${shown} of ${diff.total} changes.`
      : `${diff.total} ${noun}.`;
  }
  if (diff.added === 0 && diff.removed === 0) return "No differences.";
  return `${diff.added} added, ${diff.removed} removed${diff.truncated ? " (long; shortened)" : ""}.`;
}
