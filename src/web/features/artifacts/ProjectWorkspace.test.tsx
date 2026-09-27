// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { TeamWorkspace } from "../teams/TeamWorkspace";

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
  throw new Error("Timed out waiting for participant projects");
}

describe("participant project entry", () => {
  it("reaches project creation after choosing an event", async () => {
    window.history.pushState({}, "", "/?workspace=w");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (url: string) => {
        const path = String(url);
        const body = path.endsWith("participant-events/")
          ? [{ public_id: "e", name: "Hack" }]
          : path.endsWith("my-team/")
            ? { team: null, my_role: null }
            : [];
        return { ok: true, status: 200, json: async () => body };
      }),
    );
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () => {
      root.render(<TeamWorkspace workspaceId="w" />);
    });
    await waitFor(() => container.querySelector("select") !== null);
    const selector = container.querySelector("select") as HTMLSelectElement;
    await act(async () => {
      selector.value = "e";
      selector.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await waitFor(
      () => container.querySelector('[aria-label="My projects"]') !== null,
    );
    expect(container.textContent).toContain("Create project");
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});
