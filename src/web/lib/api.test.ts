import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "./api";
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
