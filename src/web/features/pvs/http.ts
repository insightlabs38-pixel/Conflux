import { useCallback, useEffect, useState } from "react";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function messageOf(value: unknown): string {
  if (typeof value === "string") return value;
  if (value instanceof Error) return value.message;
  if (Array.isArray(value)) return value.map(messageOf).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) =>
        key === "detail" || key === "non_field_errors"
          ? messageOf(item)
          : `${key}: ${messageOf(item)}`,
      )
      .join(" ");
  return "Request failed.";
}

export async function api<T>(
  url: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let detail: unknown = `Request failed (${response.status}).`;
    try {
      detail = await response.json();
    } catch {
      // Keep the HTTP status.
    }
    throw new ApiError(messageOf(detail), response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type Loaded<T> = {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
};

/** GET `url` (skipped while null) and re-fetch on demand. */
export function useLoad<T>(url: string | null): Loaded<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(url !== null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (url === null) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    api<T>(url)
      .then((value) => {
        if (active) setData(value);
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setData(null);
        setError(
          cause instanceof ApiError ? cause : new ApiError(messageOf(cause), 0),
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [url, attempt]);
  const reload = useCallback(() => setAttempt((count) => count + 1), []);
  return { data, error, loading, reload };
}

export const eventBase = (workspaceId: string, eventId: string) =>
  `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;

export function formatWhen(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "";
}
