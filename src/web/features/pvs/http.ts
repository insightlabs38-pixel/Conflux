import {
  ApiError,
  apiRequest,
  serverMessage,
  type RequestOptions,
} from "../../lib/api";

export { ApiError };

export { serverMessage as messageOf } from "../../lib/api";

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
      detail === undefined
        ? `Request failed (${status}).`
        : serverMessage(detail),
  });
}

export { useLoad, type Loaded } from "../../hooks/useLoad";

export const eventBase = (workspaceId: string, eventId: string) =>
  `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;

export function formatWhen(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "";
}
