// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { FrozenSubmissionPreview } from "./FrozenSubmissionPreview";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());
it("never offers a download for evidence that drifted, even with an unexpected URL", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        version: 2,
        verified: false,
        artifacts: [
          {
            id: "a",
            title: "Changed evidence",
            kind: "document",
            drift: "content_changed",
            download_url: "https://example.com/stale",
          },
        ],
      }),
    })),
  );
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(<FrozenSubmissionPreview base="/project/" stageId="s" />),
  );
  expect(container.textContent).toContain(
    "Evidence changed since finalization",
  );
  expect(container.textContent).toContain("Changed evidence");
  expect(container.querySelector("a")).toBeNull();
  expect(container.querySelector("iframe, object, video")).toBeNull();
  await act(async () => root.unmount());
});
