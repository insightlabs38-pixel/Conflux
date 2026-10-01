/**
 * The client half of provenance (PD-F002-B02-T07). The server records what a result was made from,
 * by whom and under which rules (`core/provenance.py`); the browser only shows it, and can check a
 * downloaded file against the digest the record holds. It never invents or edits a record.
 */
export type ProvenanceRef = { kind: string; id: string; label?: string };

export type Provenance = {
  version: number;
  by: { public_id: string; username: string } | null;
  at: string;
  source: { kind: string; id: string };
  inputs: { digest: string | null; refs: ProvenanceRef[] };
  rules: { name: string; version: number | string } | null;
  output: { name: string; bytes: number; sha256: string } | null;
  summary: string;
  changes: {
    total: number;
    added: number;
    removed: number;
    changed: number;
    moved: number;
  } | null;
};

/** Reads an unknown value as a provenance record, or null when it is not one. */
export function asProvenance(value: unknown): Provenance | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Partial<Provenance>;
  return typeof record.summary === "string" &&
    record.source &&
    typeof record.source.kind === "string" &&
    record.inputs &&
    Array.isArray(record.inputs.refs)
    ? (record as Provenance)
    : null;
}

/** SHA-256 of a file as lowercase hex, or null where the browser cannot compute it. */
export async function sha256Hex(data: ArrayBuffer): Promise<string | null> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) return null;
  const digest = new Uint8Array(await subtle.digest("SHA-256", data));
  return Array.from(digest, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

/** "3 changes (1 added, 2 changed)" for the counts of a restore. */
export function changeSummary(changes: NonNullable<Provenance["changes"]>) {
  const parts = (["added", "removed", "changed", "moved"] as const)
    .filter((key) => changes[key] > 0)
    .map((key) => `${changes[key]} ${key}`);
  return `${changes.total} change${changes.total === 1 ? "" : "s"}${parts.length ? ` (${parts.join(", ")})` : ""}`;
}
