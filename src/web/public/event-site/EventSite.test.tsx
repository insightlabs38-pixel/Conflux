// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EventSite } from "./EventSite";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

async function waitFor(check: () => boolean, timeoutMs = 1000) {
  const start = Date.now();
  while (!check()) {
    if (Date.now() - start > timeoutMs) throw new Error("waitFor timed out");
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
}

describe("EventSite", () => {
  it("renders the event name, schedule, tracks and prizes once loaded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: unknown) => {
        const url = String(input);
        if (url.includes("/voting/")) {
          return { ok: false, status: 404, json: async () => ({}) };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({
            public_id: "e1",
            name: "Regionals",
            description: "A great event.",
            timezone: "UTC",
            starts_at: "2026-01-01T00:00:00Z",
            ends_at: "2026-01-02T00:00:00Z",
            status: "open",
            tracks: [{ public_id: "t1", name: "AI", description: "" }],
            base_prizes: [
              {
                public_id: "p1",
                name: "Best AI",
                description: "",
                kind: "swag",
                amount: null,
                currency: "",
                track: "t1",
              },
            ],
          }),
        };
      }),
    );
    act(() => {
      root.render(<EventSite eventId="e1" />);
    });
    await waitFor(() => container.textContent?.includes("Regionals") ?? false);
    expect(container.textContent).toContain("A great event.");
    expect(container.textContent).toContain("AI");
    expect(container.textContent).toContain("Best AI");
    expect(container.querySelector('h1')?.textContent).toBe("Regionals");
  });

  it("shows an error state with retry when the event cannot be loaded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }),
    );
    act(() => {
      root.render(<EventSite eventId="missing" />);
    });
    await waitFor(() => container.querySelector('[role="alert"]') !== null);
    expect(container.textContent).toContain("Event not found");
  });
});
