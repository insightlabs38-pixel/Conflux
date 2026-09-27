// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { ArtifactPanel } from "./ArtifactPanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Timed out waiting for artifact UI");
}

function mockApi(uploadStatus: number) {
  const fetcher = vi
    .fn()
    .mockImplementation(async (input: unknown, options?: RequestInit) => {
      const url = String(input);
      const method = options?.method ?? "GET";
      let status = 200;
      let body: unknown = {};
      if (url.endsWith("preflight/")) body = { status: "READY", checks: [] };
      else if (url.endsWith("artifacts/") && method === "GET") body = [];
      else if (url.endsWith("upload-intents/") && method === "POST") {
        status = 201;
        body = {
          artifact: { public_id: "a1" },
          intent: "i1",
          upload: {
            mode: "single",
            url: "/signed-object",
            headers: { "Content-Type": "text/plain" },
          },
        };
      } else if (url === "/signed-object") status = uploadStatus;
      else if (url.endsWith("complete/")) body = { status: "uploaded" };
      else if (url.endsWith("validate/"))
        body = {
          status: "ready",
          validation: { outcome: "ok", detail: "Verified." },
        };
      return {
        ok: status < 400,
        status,
        json: async () => body,
        headers: new Headers(),
      };
    });
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

async function mountAndUpload() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => {
    root.render(<ArtifactPanel workspaceId="w" eventId="e" projectId="p" />);
  });
  await waitFor(
    () => container.textContent?.includes("All checks passed.") ?? false,
  );
  const form = container.querySelector("form") as HTMLFormElement;
  const title = form.querySelector(
    'input:not([type="file"])',
  ) as HTMLInputElement;
  const fileInput = form.querySelector(
    'input[type="file"]',
  ) as HTMLInputElement;
  await act(async () => {
    title.value = "Proof";
    title.dispatchEvent(new Event("input", { bubbles: true }));
    Object.defineProperty(fileInput, "files", {
      configurable: true,
      value: [new File(["test"], "proof.txt", { type: "text/plain" })],
    });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
  });
  return { container, root };
}

describe("artifact upload UI", () => {
  it("uploads, completes and validates through the signed URL", async () => {
    const fetcher = mockApi(200);
    const { container, root } = await mountAndUpload();
    await waitFor(
      () =>
        container.textContent?.includes("Evidence uploaded and ready.") ??
        false,
    );
    expect(
      fetcher.mock.calls.some(
        ([url, options]) =>
          url === "/signed-object" && options.method === "PUT",
      ),
    ).toBe(true);
    expect(
      fetcher.mock.calls.some(([url]) => String(url).endsWith("complete/")),
    ).toBe(true);
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });

  it("shows a failed signed upload and does not complete it", async () => {
    const fetcher = mockApi(403);
    const { container, root } = await mountAndUpload();
    await waitFor(() => container.querySelector('[role="alert"]') !== null);
    expect(container.querySelector('[role="alert"]')?.textContent).toContain(
      "Upload failed (403)",
    );
    expect(
      fetcher.mock.calls.some(([url]) => String(url).endsWith("complete/")),
    ).toBe(false);
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});
