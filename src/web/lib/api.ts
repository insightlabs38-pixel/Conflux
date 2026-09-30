import {
  ApiError as SdkApiError,
  ConfluxClient,
  operations,
  type Operations,
} from "@conflux/sdk";

/**
 * The only place the frontend talks to the network (PD-B04-T02/T03). Everything here shares one
 * error model and one policy (credentials, JSON, cancellation):
 *
 * - `apiCall(operation, args)` is the default: the generated, typed client (`sdks/typescript`), so
 *   paths, methods, parameters, bodies and responses are checked against the OpenAPI contract.
 * - `apiRequest(path)` is the compatibility path for call sites not yet moved to a typed operation
 *   (and for free-form tools such as the API explorer). `lib/transport.test.ts` ratchets raw
 *   `fetch` and untyped use down; new code must use `apiCall`.
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

type Common = {
  signal?: AbortSignal;
  /** Customise the error message for a failed response (defaults to the server's `detail`). */
  describe?: (status: number, detail: unknown) => string;
};
export type RequestOptions = Common & {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON-serialisable body. */
  body?: unknown;
};

function detailText(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    const record = detail as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
  }
  return null;
}

function failure(
  status: number,
  detail: unknown,
  describe: Common["describe"],
) {
  return new ApiError(
    status,
    describe?.(status, detail) ??
      detailText(detail) ??
      `Request failed (${status}).`,
    detail,
  );
}

/** Typed call of a generated operation, e.g. `apiCall("get_api_v1_accounts_me", {})`. */
export async function apiCall<K extends keyof Operations>(
  operation: K,
  args: Operations[K]["request"],
  { signal, describe }: Common = {},
): Promise<Operations[K]["response"]> {
  const origin =
    typeof window === "undefined" ? "http://localhost" : window.location.origin;
  const client = new ConfluxClient(origin, {
    // Same-origin relative URL, exactly as the app has always requested it.
    fetcher: (url, init) =>
      fetch(url instanceof URL ? url.pathname + url.search : url, {
        ...init,
        signal,
      }),
  });
  try {
    return await client.call(operation, args);
  } catch (error) {
    if (error instanceof SdkApiError)
      throw failure(error.status, error.body, describe);
    throw error;
  }
}

type Route = {
  operation: keyof Operations;
  method: string;
  pattern: RegExp;
  /** Parameter names in the order they occur in the path template. */
  params: string[];
  literal: number;
};

let catalog: Route[] | undefined;

function routes(): Route[] {
  catalog ??= (
    Object.entries(operations) as [
      keyof Operations,
      (typeof operations)[keyof Operations],
    ][]
  ).map(([operation, spec]) => {
    const pattern = spec.path
      .split(/\{[^}]+\}/)
      .map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("([^/]+)");
    return {
      operation,
      method: spec.method,
      pattern: new RegExp(`^${pattern}$`),
      params: [...spec.path.matchAll(/\{([^}]+)\}/g)].map((m) => m[1]),
      literal: spec.path.replace(/\{[^}]+\}/g, "").length,
    };
  });
  return catalog;
}

/** The documented operation for a method and URL path, or null when the contract has none. */
export function resolveOperation(
  method: string,
  pathname: string,
): { operation: keyof Operations; path: Record<string, string> } | null {
  let best: { route: Route; match: RegExpMatchArray } | null = null;
  for (const route of routes()) {
    if (route.method !== method) continue;
    const match = pathname.match(route.pattern);
    if (match && (!best || route.literal > best.route.literal))
      best = { route, match };
  }
  if (!best) return null;
  const path: Record<string, string> = {};
  best.route.params.forEach((name, index) => {
    path[name] = decodeURIComponent(best.match[index + 1]);
  });
  return { operation: best.route.operation, path };
}

/**
 * Request by URL. A path the OpenAPI contract documents (method, path and query parameters, body
 * allowed) is sent through the generated typed client (`apiCall`); anything else falls back to the
 * plain policy-equivalent request so undocumented or free-form URLs still work.
 */
export async function apiRequest<T>(
  path: string,
  { method = "GET", body, signal, describe }: RequestOptions = {},
): Promise<T> {
  const typed = typedCall(path, method, body);
  if (typed) {
    const result = await apiCall(typed.operation, typed.args as never, {
      signal,
      describe,
    });
    return (result === null ? undefined : result) as T;
  }
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
    throw failure(response.status, detail, describe);
  }
  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}

function typedCall(path: string, method: string, body: unknown) {
  if (!path.startsWith("/")) return null;
  const url = new URL(path, "http://localhost");
  const resolved = resolveOperation(method, url.pathname);
  if (!resolved) return null;
  const spec = operations[resolved.operation];
  if (body !== undefined && !spec.request_body) return null;
  const query: Record<string, string> = {};
  for (const [name, value] of url.searchParams) {
    if (!(spec.query_params as readonly string[]).includes(name)) return null;
    query[name] = value;
  }
  return {
    operation: resolved.operation,
    args: {
      ...(spec.path_params.length ? { path: resolved.path } : {}),
      ...(Object.keys(query).length ? { query } : {}),
      ...(body !== undefined ? { body } : {}),
    },
  };
}

/** How panels render a server problem: `field: message` pairs (nested and list values flattened). */
export function problemText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value instanceof Error) return value.message;
  if (Array.isArray(value)) return value.map(problemText).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${problemText(item)}`)
      .join(" ");
  return "Request failed.";
}

/**
 * JSON request for the workspace panels: same transport as `apiRequest`, failures raised as
 * `ApiError` whose message is `problemText` of the server's answer (or the bare status).
 */
export function apiJson<T>(
  url: string,
  method: RequestOptions["method"] = "GET",
  body?: object,
  signal?: AbortSignal,
): Promise<T> {
  return apiRequest<T>(url, {
    method,
    body,
    signal,
    describe: describeProblem,
  });
}

/** `describe` for panels: the server's problem as `field: message` pairs, or the bare status. */
export function describeProblem(status: number, detail: unknown): string {
  return detail === undefined
    ? `Request failed (${status}).`
    : problemText(detail);
}

/** Resolves to null when the request failed with one of `statuses` (an expected "not there/not yours"). */
export async function orNull<T>(
  request: Promise<T>,
  ...statuses: number[]
): Promise<T | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && statuses.includes(error.status))
      return null;
    throw error;
  }
}

/** A server answer as one line: `detail`/`non_field_errors` bare, other fields as `field: message`. */
export function serverMessage(value: unknown): string {
  if (typeof value === "string") return value;
  if (value instanceof Error) return value.message;
  if (Array.isArray(value)) return value.map(serverMessage).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) =>
        key === "detail" || key === "non_field_errors"
          ? serverMessage(item)
          : `${key}: ${serverMessage(item)}`,
      )
      .join(" ");
  return "Request failed.";
}
