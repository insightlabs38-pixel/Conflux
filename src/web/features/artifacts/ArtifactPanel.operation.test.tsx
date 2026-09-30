// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ArtifactPanel } from "./ArtifactPanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 200; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Timed out waiting for artifact UI");
}

/** A multipart upload whose part PUTs the test controls. */
function stub() {
  const parts: {
    url: string;
    signal?: AbortSignal | null;
    finish: (status: number) => void;
  }[] = [];
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      calls.push(`${method} ${url}`);
      if (url.startsWith("/part-"))
        return new Promise((resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("aborted", "AbortError")),
          );
          parts.push({
            url,
            signal: init?.signal,
            finish: (status) =>
              resolve({
                ok: status < 400,
                status,
                headers: new Headers({ ETag: `"e-${url}"` }),
              }),
          });
        });
      if (url.endsWith("preflight/"))
        return jsonResponse(200, { status: "READY", checks: [] });
      if (url.endsWith("upload-intents/"))
        return jsonResponse(201, {
          artifact: { public_id: "a1" },
          intent: "i1",
          upload: {
            mode: "multipart",
            urls: ["/part-1", "/part-2", "/part-3"],
            part_size: 2,
          },
        });
      if (url.endsWith("complete/")) return jsonResponse(200, {});
      if (url.endsWith("validate/"))
        return jsonResponse(200, { status: "ready", validation: null });
      return jsonResponse(200, []);
    }),
  );
  return { parts, calls };
}

async function mount() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      withQuery(<ArtifactPanel workspaceId="w" eventId="e" projectId="p" />),
    ),
  );
  await waitFor(
    () => container.textContent?.includes("All checks passed.") ?? false,
  );
  return { container, root };
}

async function startUpload(container: HTMLElement) {
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
      value: [new File(["abcdef"], "proof.bin")],
    });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
  });
}
const button = (container: HTMLElement, label: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === label,
  );

describe("evidence upload follows the async-operation contract", () => {
  it("shows per-part progress, disables the form while running, and finishes with the ready message", async () => {
    const { parts } = stub();
    const { container } = await mount();
    await startUpload(container);
    await waitFor(() => parts.length === 1);
    const bar = container.querySelector("progress")!;
    expect([bar.value, bar.max]).toEqual([0, 3]);
    expect(container.textContent).toContain("Uploading part 1 of 3…");
    expect(button(container, "Upload")?.disabled).toBe(true);
    for (const expected of [2, 3]) {
      await act(async () => parts[expected - 2].finish(200));
      await waitFor(() => parts.length === expected);
    }
    await act(async () => parts[2].finish(200));
    await waitFor(
      () =>
        container.textContent?.includes("Evidence uploaded and ready.") ??
        false,
    );
    expect(button(container, "Upload")?.disabled).toBe(false);
  });

  it("cancels mid-transfer: aborts the request, completes nothing and reports Cancelled", async () => {
    const { parts, calls } = stub();
    const { container } = await mount();
    await startUpload(container);
    await waitFor(() => parts.length === 1);
    await act(async () => button(container, "Cancel")?.click());
    expect(parts[0].signal?.aborted).toBe(true);
    await waitFor(() => container.textContent?.includes("Cancelled") ?? false);
    expect(container.querySelector('[role="alert"]')).toBeNull();
    expect(calls.some((call) => call.endsWith("complete/"))).toBe(false);
    expect(button(container, "Upload")?.disabled).toBe(false);
  });

  it("offers no cancel once every part is stored and the upload is being finalized", async () => {
    const { parts } = stub();
    const gate: { release?: () => void } = {};
    const { container } = await mount();
    const original = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) =>
        String(input).endsWith("complete/")
          ? new Promise((resolve) => {
              gate.release = () => resolve(jsonResponse(200, {}));
            })
          : original(input as RequestInfo, init),
      ),
    );
    await startUpload(container);
    for (let index = 0; index < 3; index++) {
      await waitFor(() => parts.length === index + 1);
      await act(async () => parts[index].finish(200));
    }
    await waitFor(
      () => container.textContent?.includes("Verifying upload…") ?? false,
    );
    expect(button(container, "Cancel")).toBeUndefined();
    await act(async () => gate.release?.());
    await waitFor(
      () =>
        container.textContent?.includes("Evidence uploaded and ready.") ??
        false,
    );
  });

  it("raises a failed part as an alert and Try again re-runs the upload", async () => {
    const { parts, calls } = stub();
    const { container } = await mount();
    await startUpload(container);
    await waitFor(() => parts.length === 1);
    await act(async () => parts[0].finish(500));
    await waitFor(() => container.querySelector('[role="alert"]') !== null);
    expect(container.querySelector('[role="alert"]')?.textContent).toContain(
      "Part 1 failed (500)",
    );
    expect(
      calls.filter((call) => call.endsWith("upload-intents/")),
    ).toHaveLength(1);
    await act(async () => button(container, "Try again")?.click());
    await waitFor(() => parts.length === 2);
    expect(
      calls.filter((call) => call.endsWith("upload-intents/")),
    ).toHaveLength(2);
  });
});
