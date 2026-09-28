import { describe, expect, it, vi } from "vitest";
import {
  operations,
  prepareRequest,
  requestSchema,
  responseText,
  type Entry,
} from "./contract";

const entry: Entry = {
  key: "get events",
  method: "get",
  path: "/api/v1/workspaces/{workspace_public_id}/events/",
  operationId: "get_events",
  parameters: [
    {
      in: "path",
      name: "workspace_public_id",
      required: true,
      schema: { type: "string" },
    },
    { in: "query", name: "search", schema: { type: "string" } },
  ],
};

describe("explorer request boundary", () => {
  it("encodes parameters and keeps cookie and bearer authentication separate", () => {
    const request = prepareRequest(
      entry,
      { "path:workspace_public_id": "w/a?x", "query:search": "a&b" },
      "",
      "session",
      "ignored",
    );
    expect(request.url).toBe(
      "/api/v1/workspaces/w%2Fa%3Fx/events/?search=a%26b",
    );
    expect(request.init).toMatchObject({
      method: "GET",
      credentials: "include",
      redirect: "error",
      cache: "no-store",
      headers: {},
    });
    const bearer = prepareRequest(
      entry,
      { "path:workspace_public_id": "w1" },
      "",
      "bearer",
      "token",
    );
    expect(bearer.init).toMatchObject({
      credentials: "omit",
      headers: { Authorization: "Bearer token" },
    });
  });

  it.each([
    "https://external.example/",
    "//external.example/api/v1/",
    "/api/v1/\\host/",
    "/api/v1/events/?x=1",
    "/api/v1/events/#x",
  ])("rejects unsafe route %s", (path) => {
    expect(() =>
      prepareRequest({ ...entry, path }, {}, "", "session", ""),
    ).toThrow("Only local");
  });

  it("rejects unresolved paths, dot segments, empty auth and malformed JSON", () => {
    expect(() => prepareRequest(entry, {}, "", "session", "")).toThrow(
      "Enter workspace_public_id",
    );
    expect(() =>
      prepareRequest(
        entry,
        { "path:workspace_public_id": ".." },
        "",
        "session",
        "",
      ),
    ).toThrow("dot segments");
    expect(() =>
      prepareRequest(
        entry,
        { "path:workspace_public_id": "w1" },
        "",
        "bearer",
        "",
      ),
    ).toThrow("bearer token");
    const write = {
      ...entry,
      method: "post",
      requestBody: { required: true, content: { "application/json": {} } },
    };
    expect(() =>
      prepareRequest(
        write,
        { "path:workspace_public_id": "w1" },
        "broken",
        "session",
        "",
      ),
    ).toThrow();
    expect(() =>
      prepareRequest(
        write,
        { "path:workspace_public_id": "w1" },
        "",
        "session",
        "",
      ),
    ).toThrow("JSON request body");
    expect(
      prepareRequest(
        write,
        { "path:workspace_public_id": "w1" },
        '{"name":"Example"}',
        "session",
        "",
      ).init,
    ).toMatchObject({
      body: '{"name":"Example"}',
      headers: { "Content-Type": "application/json" },
    });
  });

  it("serializes scalar arrays and refuses unsupported structured inputs", () => {
    const list = {
      ...entry,
      parameters: [{ in: "query", name: "ids", schema: { type: "array" } }],
    };
    expect(
      prepareRequest(
        { ...list, path: "/api/v1/events/" },
        { "query:ids": '["a","b"]' },
        "",
        "session",
        "",
      ).url,
    ).toBe("/api/v1/events/?ids=a&ids=b");
    expect(() =>
      prepareRequest(list, { "query:ids": "[{}]" }, "", "session", ""),
    ).toThrow("scalar");
    expect(() =>
      prepareRequest(
        {
          ...entry,
          parameters: [
            { in: "query", name: "object", schema: { type: "object" } },
          ],
        },
        { "query:object": "{}" },
        "",
        "session",
        "",
      ),
    ).toThrow("structured query");
    expect(() =>
      prepareRequest(
        { ...entry, requestBody: { content: { "multipart/form-data": {} } } },
        {},
        "",
        "session",
        "",
      ),
    ).toThrow();
  });
});

it("loads only operations and expands the top-level request schema", () => {
  const document = {
    openapi: "3.0.3",
    paths: {
      "/api/v1/events/": {
        parameters: [{ in: "query", name: "offset" }],
        get: { operationId: "list" },
        post: {
          operationId: "create",
          requestBody: {
            content: {
              "application/json": {
                schema: { $ref: "#/components/schemas/Event" },
              },
            },
          },
        },
      },
    },
    components: { schemas: { Event: { type: "object" } } },
  };
  const rows = operations(document);
  expect(rows).toHaveLength(2);
  expect(rows[0].parameters).toEqual([{ in: "query", name: "offset" }]);
  expect(requestSchema(rows[1], document)).toEqual({ type: "object" });
  expect(() => operations({ ...document, openapi: "invalid" })).toThrow(
    "OpenAPI 3",
  );
});

it("bounds response reads and cancels oversized streams", async () => {
  const cancel = vi.fn();
  let index = 0;
  const response = new Response(
    new ReadableStream({
      pull(controller) {
        controller.enqueue(
          new TextEncoder().encode(index++ === 0 ? "abc" : "def"),
        );
      },
      cancel,
    }),
  );
  expect(await responseText(response, 4)).toBe(
    "abcd\n[Response truncated at 1 MiB]",
  );
  expect(cancel).toHaveBeenCalledOnce();
  expect(await responseText(new Response("Café"))).toBe("Café");
  expect(await responseText(new Response(null))).toBe("");
});
