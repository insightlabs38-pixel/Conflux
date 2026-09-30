import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, apiRequest, type RequestOptions } from "../../lib/api";

export { ApiError };

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

/** Request `url` through the shared transport (lib/api.ts); failures carry the server's message. */
export function api<T>(
  url: string,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | string = "GET",
  body?: object,
  signal?: AbortSignal,
): Promise<T> {
  return apiRequest<T>(url, {
    method: method as RequestOptions["method"],
    body: body || undefined,
    signal,
    describe: (status, detail) =>
      detail === undefined ? `Request failed (${status}).` : messageOf(detail),
  });
}

export type Loaded<T> = {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
};

/**
 * GET `url` (skipped while null) on the server-state layer: concurrent users of the same URL share
 * one request, it is cancelled on unmount, and it always revalidates on mount (staleTime 0) so
 * panels never show data older than their last visit. Failures surface at once with the panel's own
 * "Try again" (`reload`); there is no silent backoff retry that would delay the error state.
 */
export function useLoad<T>(url: string | null): Loaded<T> {
  const query = useQuery({
    queryKey: ["load", url],
    queryFn: ({ signal }) => api<T>(url as string, "GET", undefined, signal),
    enabled: url !== null,
    staleTime: 0,
    retry: false,
  });
  const failed = query.isError && !query.isFetching;
  const error = failed
    ? query.error instanceof ApiError
      ? query.error
      : new ApiError(0, messageOf(query.error))
    : null;
  const reload = useCallback(() => void query.refetch(), [query]);
  return {
    data: failed || url === null ? null : (query.data ?? null),
    error,
    loading: url !== null && query.isFetching,
    reload,
  };
}

export const eventBase = (workspaceId: string, eventId: string) =>
  `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;

export function formatWhen(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "";
}
