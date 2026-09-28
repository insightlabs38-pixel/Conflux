export type Schema = {
  $ref?: string;
  type?: string;
  format?: string;
  enum?: unknown[];
  items?: Schema;
  [key: string]: unknown;
};
export type Parameter = {
  name: string;
  in: string;
  required?: boolean;
  description?: string;
  style?: string;
  explode?: boolean;
  schema?: Schema;
};
export type Operation = {
  operationId: string;
  summary?: string;
  description?: string;
  parameters?: Parameter[];
  requestBody?: {
    required?: boolean;
    content: Record<string, { schema?: Schema }>;
  };
  security?: Record<string, string[]>[];
  responses?: Record<string, unknown>;
};
export type Document = {
  openapi: string;
  paths: Record<string, Record<string, unknown>>;
  components?: { schemas?: Record<string, Schema> };
};
export type Entry = Operation & { method: string; path: string; key: string };
export type SeedExample = {
  label: string;
  method: string;
  path: string;
  body?: unknown;
};

const METHODS = new Set([
  "get",
  "post",
  "put",
  "patch",
  "delete",
  "head",
  "options",
]);

export function operations(document: Document): Entry[] {
  if (!document.openapi?.startsWith("3.") || !document.paths)
    throw new Error("The server did not return an OpenAPI 3 schema.");
  return Object.entries(document.paths)
    .flatMap(([path, methods]) =>
      Object.entries(methods)
        .filter(([method]) => METHODS.has(method))
        .map(([method, value]) => {
          const operation = value as Operation;
          return {
            ...operation,
            parameters: [
              ...((methods.parameters as Parameter[] | undefined) ?? []),
              ...(operation.parameters ?? []),
            ],
            path,
            method,
            key: `${method} ${path}`,
          };
        }),
    )
    .sort(
      (a, b) =>
        a.path.localeCompare(b.path) || a.method.localeCompare(b.method),
    );
}

export function requestSchema(
  entry: Entry,
  document: Document,
): Schema | undefined {
  const schema = entry.requestBody?.content["application/json"]?.schema;
  if (schema?.$ref?.startsWith("#/components/schemas/"))
    return (
      document.components?.schemas?.[
        schema.$ref.slice("#/components/schemas/".length)
      ] ?? schema
    );
  return schema;
}

export function prepareRequest(
  entry: Entry,
  values: Record<string, string>,
  body: string,
  auth: "session" | "bearer",
  token: string,
): { url: string; init: RequestInit } {
  if (
    !METHODS.has(entry.method) ||
    !entry.path.startsWith("/api/v1/") ||
    /[?#\\]|\/\//.test(entry.path)
  )
    throw new Error("Only local API v1 routes can be sent.");
  let path = entry.path;
  if (
    path
      .split("/")
      .some((segment) => [".", ".."].includes(decodeURIComponent(segment)))
  )
    throw new Error("Path segments cannot be dot segments.");
  const query = new URLSearchParams();
  for (const parameter of entry.parameters ?? []) {
    const value = values[`${parameter.in}:${parameter.name}`]?.trim() ?? "";
    if (parameter.required && !value)
      throw new Error(`Enter ${parameter.name}.`);
    if (!value) continue;
    if (parameter.in === "path") {
      if (value === "." || value === "..")
        throw new Error("Path segments cannot be dot segments.");
      path = path.replaceAll(`{${parameter.name}}`, encodeURIComponent(value));
    } else if (parameter.in === "query") {
      if (
        parameter.schema?.type === "object" ||
        (parameter.style && parameter.style !== "form")
      )
        throw new Error(
          `Use an SDK for the structured query parameter ${parameter.name}.`,
        );
      if (parameter.schema?.type === "array") {
        const items: unknown = JSON.parse(value);
        if (
          !Array.isArray(items) ||
          items.some(
            (item) => !["string", "number", "boolean"].includes(typeof item),
          )
        )
          throw new Error(
            `${parameter.name} must be a JSON array of scalar values.`,
          );
        if (parameter.explode === false)
          query.append(parameter.name, items.join(","));
        else
          items.forEach((item) => query.append(parameter.name, String(item)));
      } else query.append(parameter.name, value);
    } else
      throw new Error(
        `Use an SDK for the ${parameter.in} parameter ${parameter.name}.`,
      );
  }
  if (/[{}]/.test(path)) throw new Error("Fill every path parameter.");
  const headers: Record<string, string> = {};
  if (auth === "bearer") {
    if (!token.trim() || /[\r\n]/.test(token))
      throw new Error("Enter a valid bearer token.");
    headers.Authorization = `Bearer ${token.trim()}`;
  }
  const init: RequestInit = {
    method: entry.method.toUpperCase(),
    headers,
    credentials: auth === "session" ? "include" : "omit",
    redirect: "error",
    cache: "no-store",
  };
  if (entry.requestBody) {
    if (!entry.requestBody.content["application/json"])
      throw new Error("Use an SDK for this route's non-JSON request body.");
    if (["get", "head"].includes(entry.method))
      throw new Error("GET/HEAD bodies are unsupported.");
    if (body.trim()) {
      JSON.parse(body);
      headers["Content-Type"] = "application/json";
      init.body = body;
    } else if (entry.requestBody.required)
      throw new Error("Enter a JSON request body.");
  }
  return { url: path + (query.size ? `?${query}` : ""), init };
}

export async function responseText(
  response: Response,
  limit = 1024 * 1024,
): Promise<string> {
  if (!response.body) return "";
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let bytes = 0;
  let text = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) return text + decoder.decode();
      const remaining = limit - bytes;
      text += decoder.decode(value.subarray(0, remaining), { stream: true });
      bytes += value.byteLength;
      if (bytes > limit) {
        await reader.cancel();
        return text + decoder.decode() + "\n[Response truncated at 1 MiB]";
      }
    }
  } finally {
    reader.releaseLock();
  }
}
