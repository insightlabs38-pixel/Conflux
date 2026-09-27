import { describe, expect, it, vi } from "vitest";
import { ApiError, ConfluxClient } from "../../sdks/typescript";

describe("generated TypeScript SDK", () => {
  it("encodes a scoped path and sends bearer authentication", async () => {
    const fetcher = vi.fn(
      async (_url: URL, _options: RequestInit) =>
        new Response(JSON.stringify([{ action: "test" }]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    const client = new ConfluxClient("https://example.test", {
      bearerToken: "secret",
      fetcher: fetcher as typeof fetch,
    });
    const result = await client.call("get_api_v1_audit_workspace_public_id", {
      path: { workspace_public_id: "a/b" },
    });
    expect(result).toEqual([{ action: "test" }]);
    expect(String(fetcher.mock.calls[0][0])).toBe(
      "https://example.test/api/v1/audit/a%2Fb/",
    );
    expect(fetcher.mock.calls[0][1].headers).toMatchObject({
      Authorization: "Bearer secret",
    });
  });

  it("returns null for no content and preserves error responses", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "denied" }), { status: 403 }),
      );
    const client = new ConfluxClient("https://example.test", {
      fetcher: fetcher as typeof fetch,
    });
    expect(await client.call("post_api_v1_accounts_logout", {})).toBeNull();
    await expect(
      client.call("get_api_v1_accounts_me", {}),
    ).rejects.toMatchObject({
      status: 403,
      body: { detail: "denied" },
    } satisfies Partial<ApiError>);
  });
});
