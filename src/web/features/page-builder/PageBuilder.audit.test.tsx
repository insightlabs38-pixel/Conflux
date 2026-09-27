// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { PageBuilder } from "./PageBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Page builder did not update");
}

it("shows accessibility warnings returned by the audit endpoint", async () => {
  const fetchMock = vi.fn().mockImplementation(async (input: unknown) => {
    const url = String(input);
    if (url.endsWith("accessibility-audit/"))
      return {
        ok: true,
        json: async () => [
          {
            category: "heading",
            severity: "warning",
            message:
              "More than one hero block on this page means more than one h1.",
            block_public_id: "b1",
          },
        ],
      };
    if (url.endsWith("/blocks/")) return { ok: true, json: async () => [] };
    if (url.endsWith("/page/"))
      return {
        ok: true,
        json: async () => ({ public_id: "p1", theme: "default" }),
      };
    throw new Error(`Unexpected request: ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<PageBuilder workspaceId="w1" eventId="e1" />));

  await until(
    () => container.textContent?.includes("more than one h1") ?? false,
  );
  expect(container.textContent).toContain("Accessibility warnings");

  act(() => root.unmount());
  container.remove();
});

it("shows no accessibility warnings section when the audit is clean", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: unknown) => {
      const url = String(input);
      if (url.endsWith("accessibility-audit/"))
        return { ok: true, json: async () => [] };
      if (url.endsWith("/blocks/")) return { ok: true, json: async () => [] };
      return {
        ok: true,
        json: async () => ({ public_id: "p1", theme: "default" }),
      };
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<PageBuilder workspaceId="w1" eventId="e1" />));

  await until(() => container.textContent?.includes("no blocks yet") ?? false);
  expect(container.textContent).not.toContain("Accessibility warnings");

  act(() => root.unmount());
  container.remove();
});
