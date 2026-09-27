import { operations, type Operations } from "./generated.js";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: unknown,
  ) {
    super(`Conflux API returned ${status}`);
  }
}

export class ConfluxClient {
  constructor(
    private readonly baseUrl: string,
    private readonly options: {
      bearerToken?: string;
      fetcher?: typeof fetch;
    } = {},
  ) {}

  async call<K extends keyof Operations>(
    operation: K,
    args: Operations[K]["request"],
  ): Promise<Operations[K]["response"]> {
    const spec = operations[operation];
    let path: string = spec.path;
    const request = args as {
      path?: Record<string, string | number>;
      query?: Record<string, string | number | boolean | undefined>;
      body?: unknown;
    };
    for (const name of spec.path_params) {
      const value = request.path?.[name];
      if (value === undefined || value === null) {
        throw new Error(`Missing path parameter: ${name}`);
      }
      path = path.replace(`{${name}}`, encodeURIComponent(String(value)));
    }
    const url = new URL(path, this.baseUrl);
    for (const [name, value] of Object.entries(request.query ?? {})) {
      if (!(spec.query_params as readonly string[]).includes(name)) {
        throw new Error(`Unknown query parameter: ${name}`);
      }
      if (value !== undefined && value !== null) {
        url.searchParams.set(name, String(value));
      }
    }
    const headers: Record<string, string> = {};
    if (this.options.bearerToken) {
      headers.Authorization = `Bearer ${this.options.bearerToken}`;
    }
    if (request.body !== undefined) {
      if (!spec.request_body) {
        throw new Error(
          `Operation does not accept a JSON body: ${String(operation)}`,
        );
      }
      headers["Content-Type"] = "application/json";
    }
    const fetcher = this.options.fetcher ?? fetch;
    const response = await fetcher(url, {
      method: spec.method,
      credentials: "include",
      headers,
      body:
        request.body === undefined ? undefined : JSON.stringify(request.body),
    });
    if (!response.ok) {
      const raw = await response.text();
      let body: unknown = raw;
      try {
        body = JSON.parse(raw);
      } catch {
        // A non-JSON response remains available to callers as text.
      }
      throw new ApiError(response.status, body);
    }
    if (response.status === 204 || spec.response_kind === "none") {
      return null as Operations[K]["response"];
    }
    return (
      spec.response_kind === "json"
        ? await response.json()
        : await response.text()
    ) as Operations[K]["response"];
  }
}
