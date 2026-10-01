// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { ConfigHistoryPanel } from "./ConfigHistoryPanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";

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
  act(() =>
    root.render(
      withQuery(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
    ),
  );
  await until(() => container.textContent?.includes("event.updated") ?? false);
  expect(container.textContent).toContain("Hack 2.0");
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/audit/w1/events/e1/config-history/",
    expect.objectContaining({ credentials: "include" }),
  );
  act(() => root.unmount());
  container.remove();
});

it("draws the server's diff of each field and falls back to before and after without one", async () => {
  const entry = (id: string, diff?: object) => ({
    public_id: id,
    actor: "organizer",
    action: "event.updated",
    resource_type: "Event",
    resource_id: "e1",
    changes: { name: { before: "Hack", after: "Hack 2.0" } },
    ...(diff ? { diff } : {}),
    created_at: "2026-09-27T00:00:00Z",
  });
  const diff = {
    name: {
      kind: "json",
      total: 1,
      truncated: false,
      changes: [
        {
          path: "",
          op: "changed",
          before: "Hack",
          after: "Hack 2.0",
          clipped: false,
        },
      ],
    },
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => jsonResponse(200, [entry("h1", diff), entry("h2")])),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() =>
    root.render(
      withQuery(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
    ),
  );
  await until(() => container.querySelector(".cx-diff") !== null);
  const group = container.querySelector('[role="group"]')!;
  expect(group.getAttribute("aria-label")).toBe("Changes to name");
  expect(group.textContent).toContain("Changed");
  expect(group.textContent).toContain('"Hack 2.0"');
  // An entry from an older server has no diff: the flat before and after still show.
  expect(container.querySelectorAll("li")[1].textContent).toContain('"Hack"');
  expect(container.querySelectorAll(".cx-diff")).toHaveLength(1);
  act(() => root.unmount());
  container.remove();
});

it("shows the provenance of a restore when the server recorded one", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      jsonResponse(200, [
        {
          public_id: "h1",
          actor: "organizer",
          action: "event.restored",
          resource_type: "Event",
          resource_id: "e1",
          changes: { name: { before: "Hack 2.0", after: "Hack" } },
          provenance: {
            version: 1,
            by: { public_id: "u1", username: "organizer" },
            at: "2026-10-01T10:00:00Z",
            source: { kind: "config_history", id: "h0" },
            inputs: {
              digest: null,
              refs: [{ kind: "audit_event", id: "h0", label: "event.updated" }],
            },
            rules: { name: "restore_before_values", version: 1 },
            output: null,
            summary:
              "Restored 1 field of Event from the earlier change event.updated.",
            changes: { total: 1, added: 0, removed: 0, changed: 1, moved: 0 },
          },
          created_at: "2026-09-27T00:00:00Z",
        },
      ]),
    ),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() =>
    root.render(
      withQuery(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
    ),
  );
  await until(() => container.querySelector(".cx-provenance") !== null);
  const text = container.querySelector(".cx-provenance")!.textContent!;
  expect(text).toContain("Restored 1 field of Event");
  expect(text).toContain("restore_before_values (version 1)");
  expect(text).toContain("1 change (1 changed)");
  expect(text).not.toContain("SHA-256");
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
  act(() =>
    root.render(
      withQuery(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
    ),
  );
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
  act(() =>
    root.render(
      withQuery(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
    ),
  );
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
          ? jsonResponse(success ? 200 : 400, { restored: true })
          : { ok: true, json: async () => [entry] },
      );
    vi.stubGlobal("fetch", fetchMock);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(
        withQuery(<ConfigHistoryPanel workspaceId="w1" eventId="e1" />),
      ),
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
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
    act(() => root.unmount());
    container.remove();
  },
);
