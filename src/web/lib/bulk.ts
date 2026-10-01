import { ApiError, apiJson } from "./api";

/**
 * The client half of the bulk-operation planner (PD-F002-B01-T04): preview (dry run) returns the
 * exact effects and a signed token; apply re-sends the same operations with that token, is
 * all-or-nothing, and is safe to retry (the same token is never applied twice). The server owns
 * every rule; this only carries requests and describes the answers in plain language.
 */
export type BulkOperation = { action: string } & Record<string, unknown>;
export type BulkEffect = { action: string } & Record<string, unknown>;
export type BulkPreview = {
  applied: false;
  effects: BulkEffect[];
  preview_token: string;
  expires_in: number;
  /** Approvals the apply will need first (an event gate is on); see lib/approvals.ts. */
  approvals?: { action: string; label: string; summary: string[] }[];
};
export type BulkApplied = { applied: true; effects: BulkEffect[] };

export function bulkUrl(workspaceId: string, eventId: string): string {
  return `/api/v1/workspaces/${workspaceId}/events/${eventId}/operations/bulk/`;
}

export function previewBulk(
  url: string,
  operations: BulkOperation[],
): Promise<BulkPreview> {
  return apiJson<BulkPreview>(url, "POST", { operations });
}

export function applyBulk(
  url: string,
  operations: BulkOperation[],
  token: string,
): Promise<BulkApplied> {
  return apiJson<BulkApplied>(url, "POST", {
    operations,
    preview_token: token,
  });
}

/** 409 `approval_required`: held until another person approves; not a stale preview. */
export function needsApproval(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    error.status === 409 &&
    (error.detail as { code?: string } | undefined)?.code ===
      "approval_required"
  );
}
/** The sentence the server gave for a held operation. */
export function approvalMessage(error: unknown): string {
  const detail = (error as ApiError).detail as { detail?: string } | undefined;
  return detail?.detail ?? "It needs approval from another person first.";
}
/** 409: the preview no longer matches (expired, or the data changed); preview again. */
export function isStale(error: unknown): boolean {
  return (
    error instanceof ApiError && error.status === 409 && !needsApproval(error)
  );
}
/** A refusal that retrying the same request cannot fix (validation, permission). */
export function isRefusal(error: unknown): boolean {
  return error instanceof ApiError && error.status >= 400 && error.status < 500;
}

export type Names = { tracks?: Record<string, string> };

const plural = (n: number, one: string, many = `${one}s`) =>
  `${n} ${n === 1 ? one : many}`;

function projectTrackChange(effect: BulkEffect, names: Names): string {
  const changes =
    (effect.changes as { before: string | null; after: string }[]) ?? [];
  const tracks = names.tracks ?? {};
  const target = changes[0]?.after;
  const was = new Map<string, number>();
  for (const change of changes) {
    const key = change.before
      ? (tracks[change.before] ?? "another track")
      : "no track";
    was.set(key, (was.get(key) ?? 0) + 1);
  }
  const from = [...was].map(([name, n]) => `${n} from ${name}`).join(", ");
  return `Move ${plural(changes.length, "project")} to ${
    target ? (tracks[target] ?? "the track") : "the track"
  }${from ? ` (${from})` : ""}.`;
}

/** One effect in plain language; an unknown action still gets an honest generic line. */
export function describeEffect(effect: BulkEffect, names: Names = {}): string {
  switch (effect.action) {
    case "move":
      return projectTrackChange(effect, names);
    case "advance": {
      const n = (effect.advanced as unknown[] | undefined)?.length ?? 0;
      return `Advance ${plural(n, "entry", "entries")} to the next stage.`;
    }
    case "extend": {
      const n = (effect.changes as unknown[] | undefined)?.length ?? 0;
      return `Extend ${plural(n, "gate")}.`;
    }
    case "assign": {
      const n = (effect.pairs as unknown[] | undefined)?.length ?? 0;
      return `Assign judges to projects: ${plural(n, "pairing")}.`;
    }
    case "send": {
      const n = Number(effect.recipient_count ?? 0);
      return `Send a message to ${plural(n, "recipient")}.`;
    }
    default:
      return `Run ${effect.action.replace(/_/g, " ")}.`;
  }
}
