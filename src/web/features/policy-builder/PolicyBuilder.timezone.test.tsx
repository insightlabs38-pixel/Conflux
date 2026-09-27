// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PolicyBuilder } from "./PolicyBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Policy builder did not update");
}

const GATE = {
  public_id: "g1",
  name: "Submissions",
  opens_at: "2026-03-08T05:00:00Z",
  closes_at: "2026-03-08T12:00:00Z",
  event_local_opens_at: "2026-03-08T00:00:00-05:00",
  event_local_closes_at: "2026-03-08T08:00:00-04:00",
  dst_warning:
    "This window crosses a daylight-saving change in America/New_York.",
};
const TIMELINE = [
  {
    label: "Event window",
    opens_at: "2026-03-08T05:00:00Z",
    closes_at: "2026-03-09T05:00:00Z",
    event_local_opens_at: "2026-03-08T00:00:00-05:00",
    event_local_closes_at: "2026-03-09T01:00:00-04:00",
    dst_warning:
      "This window crosses a daylight-saving change in America/New_York.",
  },
];

describe("temporal gate timezone display", () => {
  it("shows the DST warning and event-local time, and creates a gate with real UTC instants", async () => {
    let created: unknown = null;
    const fetcher = vi
      .fn()
      .mockImplementation(async (path: string, options?: RequestInit) => {
        if (path.endsWith("temporal-gates/") && options?.method === "POST") {
          created = JSON.parse(String(options.body));
          return { ok: true, status: 201, json: async () => GATE };
        }
        return {
          ok: true,
          status: 200,
          json: async () => {
            if (path.endsWith("temporal-gates/")) return [GATE];
            if (path.endsWith("timezone-timeline/")) return TIMELINE;
            if (path.endsWith("policy-presets/")) return {};
            return [];
          },
        };
      });
    vi.stubGlobal("fetch", fetcher);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(<PolicyBuilder workspaceId="w" eventId="e" />),
    );
    await waitFor(
      () => container.textContent?.includes("Submissions") ?? false,
    );
    expect(container.textContent).toContain("daylight-saving change");
    expect(container.textContent).toContain("Event window");

    const gateForm = [...container.querySelectorAll("form")].find((form) =>
      form.textContent?.includes("Add gate"),
    )!;
    const nameInput =
      gateForm.querySelector<HTMLInputElement>("input:not([type])")!;
    const opens = gateForm.querySelector<HTMLInputElement>(
      'input[type="datetime-local"]',
    )!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set?.call(nameInput, "New gate");
      nameInput.dispatchEvent(new Event("input", { bubbles: true }));
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set?.call(opens, "2026-06-01T09:00");
      opens.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      const addGateButton = [...gateForm.querySelectorAll("button")].find(
        (button) => button.textContent === "Add gate",
      );
      addGateButton?.click();
    });
    await waitFor(() => created !== null);
    const body = created as {
      name: string;
      opens_at: string | null;
      closes_at: string | null;
    };
    expect(body.name).toBe("New gate");
    expect(body.opens_at).toBe(new Date("2026-06-01T09:00").toISOString());
    expect(body.closes_at).toBeNull();

    await act(async () => root.unmount());
    container.remove();
  });
});
