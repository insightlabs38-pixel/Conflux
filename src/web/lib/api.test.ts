import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  apiCall,
  apiJson,
  apiRequest,
  orNull,
  problemText,
  resolveOperation,
} from "./api";
import { jsonResponse } from "./test-http";
import { retryDelay, shouldRetry } from "./query";

afterEach(() => vi.unstubAllGlobals());
const reply = (status: number, body?: unknown) =>
  vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });

describe("apiRequest", () => {
  it("sends credentials, serialises JSON bodies and returns parsed JSON", async () => {
    const fetchMock = reply(200, { ok: 1 });
    vi.stubGlobal("fetch", fetchMock);
    const signal = new AbortController().signal;
    await expect(
      apiRequest("/api/v1/x/", { method: "POST", body: { a: 1 }, signal }),
    ).resolves.toEqual({ ok: 1 });
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/x/", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: '{"a":1}',
      signal,
    });
  });

  it("sends no body or content type for plain reads and resolves 204 to undefined", async () => {
    const fetchMock = reply(204);
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiRequest("/api/v1/x/")).resolves.toBeUndefined();
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      method: "GET",
      headers: undefined,
      body: undefined,
    });
  });

  it("raises ApiError with status, detail and a message from the server", async () => {
    vi.stubGlobal("fetch", reply(403, { detail: "Not allowed." }));
    const error = await apiRequest("/x").catch((cause) => cause);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 403,
      message: "Not allowed.",
      detail: { detail: "Not allowed." },
    });
  });

  it("lets callers describe failures, and falls back to a generic message without a body", async () => {
    vi.stubGlobal("fetch", reply(503));
    await expect(
      apiRequest("/x", { describe: (status) => `Could not load (${status}).` }),
    ).rejects.toMatchObject({ message: "Could not load (503)." });
    await expect(apiRequest("/x")).rejects.toMatchObject({
      message: "Request failed (503).",
    });
  });
});

describe("retry policy", () => {
  it.each([
    [0, new ApiError(500, "x"), true],
    [1, new ApiError(503, "x"), true],
    [0, new ApiError(429, "x"), true],
    [2, new ApiError(500, "x"), false],
    [0, new ApiError(400, "x"), false],
    [0, new ApiError(401, "x"), false],
    [0, new ApiError(403, "x"), false],
    [0, new ApiError(404, "x"), false],
    [0, new ApiError(422, "x"), false],
    [0, new TypeError("Failed to fetch"), true],
    [0, new DOMException("aborted", "AbortError"), false],
  ])("attempt %i with %s -> retry %s", (count, error, expected) => {
    expect(shouldRetry(count, error)).toBe(expected);
  });

  it("backs off exponentially up to four seconds", () => {
    expect([0, 1, 2, 3, 4].map(retryDelay)).toEqual([
      500, 1000, 2000, 4000, 4000,
    ]);
  });
});

const W = "/api/v1/workspaces/w1/events/e1";

describe("typed client routing", () => {
  it("resolves documented URLs to operations with path parameters bound by name, not order", () => {
    expect(resolveOperation("GET", "/api/v1/accounts/me/")).toEqual({
      operation: "get_api_v1_accounts_me",
      path: {},
    });
    const found = resolveOperation("GET", `${W}/projects/p%201/`);
    expect(found?.path).toEqual({
      workspace_public_id: "w1",
      event_public_id: "e1",
      project_public_id: "p 1",
    });
  });

  it("prefers a literal segment over a parameter and ignores unknown paths and other methods", () => {
    expect(
      resolveOperation("GET", `${W}/rules/acknowledgements/`)?.operation,
    ).toMatch(/rules_acknowledgements$/);
    expect(resolveOperation("GET", `${W}/rules/3/`)?.operation).toMatch(
      /rules_number$/,
    );
    expect(resolveOperation("GET", "/api/v1/not/a/route/")).toBeNull();
    expect(resolveOperation("DELETE", "/api/v1/accounts/me/")).toBeNull();
  });

  it("sends documented requests through the generated client with the app's request policy", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { username: "ada" }));
    vi.stubGlobal("fetch", fetchMock);
    const signal = new AbortController().signal;
    await expect(
      apiRequest("/api/v1/accounts/me/", { signal }),
    ).resolves.toEqual({ username: "ada" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/accounts/me/",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
        signal,
      }),
    );
  });

  it("never discards a body the schema does not describe, and maps an empty answer to undefined", async () => {
    const rows = [{ status: "pending" }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, rows)));
    await expect(
      apiRequest(`${W}/result-publication-requests/`),
    ).resolves.toEqual(rows);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(204)));
    await expect(
      apiRequest("/api/v1/accounts/logout/", { method: "POST" }),
    ).resolves.toBeUndefined();
  });

  it("falls back to the plain request for query parameters or bodies the contract does not document", async () => {
    const fetchMock = vi.fn(async (..._args: unknown[]) =>
      jsonResponse(200, { ok: 1 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await apiRequest("/api/v1/accounts/me/?debug=1");
    await apiRequest("/api/v1/accounts/logout/", {
      method: "POST",
      body: { extra: true },
    });
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/accounts/me/?debug=1");
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      body: '{"extra":true}',
      headers: { "Content-Type": "application/json" },
    });
  });

  it("raises the shared ApiError with the server detail from a typed call", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(403, { detail: "Not allowed." })),
    );
    const error = await apiCall("get_api_v1_accounts_me", {}).catch((c) => c);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 403,
      message: "Not allowed.",
      detail: { detail: "Not allowed." },
    });
    await expect(
      apiCall("get_api_v1_accounts_me", {}, { describe: (s) => `No (${s}).` }),
    ).rejects.toMatchObject({ message: "No (403)." });
  });
});

describe("panel helpers", () => {
  it("renders server problems as field: message pairs and falls back to the status", async () => {
    expect(problemText({ name: ["Too long.", "Bad."], detail: "Nope" })).toBe(
      "name: Too long. Bad. detail: Nope",
    );
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(400, { name: ["Required."] })),
    );
    await expect(apiJson("/x", "POST", { a: 1 })).rejects.toMatchObject({
      message: "name: Required.",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("<html>", { status: 502 })),
    );
    await expect(apiJson("/x")).rejects.toMatchObject({
      message: "Request failed (502).",
    });
  });

  it("orNull turns only the listed statuses into null", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(404, {})),
    );
    await expect(orNull(apiRequest("/x"), 404)).resolves.toBeNull();
    await expect(orNull(apiRequest("/x"), 403)).rejects.toMatchObject({
      status: 404,
    });
  });
});
