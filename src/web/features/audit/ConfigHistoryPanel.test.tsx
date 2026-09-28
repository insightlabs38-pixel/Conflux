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

it.each([true, false])(
  "confirms a restore and reports its result (success=%s)",
  async (success) => {
    const entry = {
      public_id: "h1",
      actor: "organizer",
      action: "stage.updated",
      resource_type: "Stage",
      resource_id: "s1",
      changes: { name: { before: "Old", after: "Current" } },
      created_at: "2026-09-28T00:00:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockImplementation(async (_url: string, options?: RequestInit) =>
        options?.method === "POST"
          ? { ok: success, status: 400, json: async () => ({ restored: true }) }
          : { ok: true, json: async () => [entry] },
      );
    vi.stubGlobal("fetch", fetchMock);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
    );
    await until(
      () => container.textContent?.includes("Restore before values") ?? false,
    );
    const button = (text: string) =>
      Array.from(container.querySelectorAll("button")).find(
        (b) => b.textContent === text,
      )!;
    await act(async () => button("Restore before values").click());
    expect(
      fetchMock.mock.calls.some(([, options]) => options?.method === "POST"),
    ).toBe(false);
    await act(async () => button("Cancel").click());
    expect(container.textContent).not.toContain("Confirm restore");
    await act(async () => button("Restore before values").click());
    await act(async () => button("Confirm restore").click());
    await until(
      () =>
        container.textContent?.includes(
          success ? "Configuration restored" : "Restore failed (400)",
        ) ?? false,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/audit/w1/events/e1/config-history/h1/restore/",
      { method: "POST", credentials: "include" },
    );
    act(() => root.unmount());
    container.remove();
  },
);
