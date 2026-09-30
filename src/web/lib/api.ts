/**
 * The single transport seam for frontend requests (PD-B04-T02). Every query/mutation goes through
 * `apiRequest`, which owns credentials, JSON bodies, cancellation and error normalization, so the
 * transport can later move onto the generated typed client (PD-B04-T03) in one place.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON-serialisable body. */
  body?: unknown;
  signal?: AbortSignal;
  /** Customise the error message for a failed response (defaults to the server's `detail`). */
  describe?: (status: number, detail: unknown) => string;
};

function detailText(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    const record = detail as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
  }
  return null;
}

export async function apiRequest<T>(
  path: string,
  { method = "GET", body, signal, describe }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => undefined);
    throw new ApiError(
      response.status,
      describe?.(response.status, detail) ??
        detailText(detail) ??
        `Request failed (${response.status}).`,
      detail,
    );
  }
  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}
