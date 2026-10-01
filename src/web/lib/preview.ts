/**
 * The client half of safe previews (PD-F002-B02-T03). The server turns a file or a link into one
 * descriptor (`core/previews.py`); the browser only draws it. Nothing in a descriptor is markup:
 * names, facts, findings and excerpts are text, and media is a download address, never inlined.
 */
export type PreviewKind =
  | "text"
  | "image"
  | "video"
  | "document"
  | "archive"
  | "data"
  | "link"
  | "unavailable";

export type Preview = {
  source: string;
  ref: Record<string, string>;
  name: string;
  content_type: string;
  size: number | null;
  kind: PreviewKind;
  detected_type: string;
  state: "ready" | "pending" | "unavailable";
  reason: { code: string; message: string } | null;
  facts: Record<string, string | number | boolean>;
  findings: {
    level: "info" | "warning" | "blocked";
    code: string;
    message: string;
  }[];
  findings_total: number;
  text: string;
  entries: { name: string; size: number | null }[];
  entries_total: number;
  media: { url: string; filename: string } | null;
  link: string | null;
  inspected_at: string | null;
};

export const previewUrl = (
  workspaceId: string,
  source: string,
  ref: Record<string, string>,
) =>
  `/api/v1/workspaces/${workspaceId}/previews/${source}/?` +
  new URLSearchParams(ref).toString();

export const KIND_LABEL: Record<PreviewKind, string> = {
  text: "Text",
  image: "Image",
  video: "Video",
  document: "Document",
  archive: "Archive",
  data: "Data",
  link: "Link",
  unavailable: "No preview",
};

const UNITS = ["B", "KB", "MB", "GB"];
/** 1536 -> "1.5 KB"; sizes are for people, so one decimal at most. */
export function humanSize(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${unit === 0 ? value : value.toFixed(1).replace(/\.0$/, "")} ${UNITS[unit]}`;
}

const BYTE_FACTS = new Set(["bytes", "uncompressed_bytes", "compressed_bytes"]);
/** A fact as a label and a value ("uncompressed_bytes", 2048 -> "Uncompressed size", "2 KB"). */
export function factRow(
  key: string,
  value: string | number | boolean,
): [string, string] {
  const label =
    key === "bytes"
      ? "size"
      : key.replace(/_bytes$/, " size").replace(/_/g, " ");
  const text =
    typeof value === "number" && BYTE_FACTS.has(key)
      ? humanSize(value)
      : String(value);
  return [label.charAt(0).toUpperCase() + label.slice(1), text];
}

/** A link is opened only when it is a web address. */
export const isWebUrl = (url: string | null): url is string =>
  !!url && /^https?:\/\//i.test(url);
