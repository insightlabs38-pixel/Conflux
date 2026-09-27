// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { ConfigHistoryPanel } from "./ConfigHistoryPanel";

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
  throw new Error("Config history panel did not update");
}

it("renders each entry's field-level before/after diff", async () => {
  const entries = [
    {
      public_id: "h1",
      actor: "organizer",
      action: "event.updated",
      resource_type: "Event",
      resource_id: "e1",
      changes: { name: { before: "Hack", after: "Hack 2.0" } },
      created_at: "2026-09-27T00:00:00Z",
    },
  ];
  const fetchMock = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => entries });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />));
  await until(() => container.textContent?.includes("event.updated") ?? false);
  expect(container.textContent).toContain("Hack 2.0");
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/audit/w1/events/e1/config-history/",
    expect.objectContaining({ credentials: "include" }),
  );
  act(() => root.unmount());
  container.remove();
});

it("shows an empty state when there is no captured history yet", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => [] }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />));
  await until(
    () => container.textContent?.includes("No recorded configuration") ?? false,
  );
  act(() => root.unmount());
  container.remove();
});

it("shows a retryable error state when the request fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />));
  await until(() => container.querySelector('[role="alert"]') !== null);
  act(() => root.unmount());
  container.remove();
});
