import { ApiError, apiJson, problemText } from "./api";
import type { VersionInfo } from "./versions";

/**
 * The client half of previewing as a role, as of a time or at a kept version (PD-F002-B03-T01).
 * The server resolves the context and builds what that person would see (`core/preview_context.py`);
 * the browser only chooses a context and draws the answer. A context is request data, never an
 * identity: it is sent in one body, nothing is stored and nothing else in the app reads it.
 */
export type PreviewContext = {
  /** A role the surface can be viewed as; null is the organizer's own view. */
  role: string | null;
  /** An instant (ISO, UTC); exclusive with `version`. */
  at: string | null;
  /** A version id of the surface's version source; null is the live one. */
  version: string | null;
};

export const LIVE: PreviewContext = { role: null, at: null, version: null };

export const isLive = (context: PreviewContext) =>
  context.role === null && context.at === null && context.version === null;

export type PreviewNotice = { code: string; message: string };

export type PreviewAs<T> = {
  surface: string;
  label: string;
  /** One sentence naming who and when; shown verbatim. */
  summary: string;
  roles: string[];
  versions: VersionInfo[];
  resolved: {
    role: string | null;
    at: string | null;
    version: VersionInfo | null;
    live: boolean;
  };
  notices: PreviewNotice[];
  data: T;
};

export const previewAsUrl = (workspaceId: string, surface: string) =>
  `/api/v1/workspaces/${workspaceId}/preview-as/${surface}/`;

const present = (context: PreviewContext) =>
  Object.fromEntries(Object.entries(context).filter(([, v]) => v !== null));

export const previewAs = <T>(
  workspaceId: string,
  surface: string,
  ref: Record<string, string>,
  context: PreviewContext,
  signal?: AbortSignal,
  input?: object,
) =>
  apiJson<PreviewAs<T>>(
    previewAsUrl(workspaceId, surface),
    "POST",
    { ref, context: present(context), ...(input ? { input } : {}) },
    signal,
  );

/** What to tell the person: the server's sentences without the parameter names they came keyed by. */
export function previewProblem(error: unknown): string {
  if (error instanceof ApiError && error.status === 400) {
    const detail = error.detail;
    if (detail && typeof detail === "object" && !Array.isArray(detail))
      return problemText(Object.values(detail));
  }
  return error instanceof Error ? error.message : "The preview failed.";
}

/** The value a `datetime-local` control shows for an instant, in the browser's time zone. */
export function toLocalInput(instant: string | null): string {
  if (!instant) return "";
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

/** The instant (ISO, UTC) a `datetime-local` value means in the browser's time zone, or null. */
export function fromLocalInput(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}
