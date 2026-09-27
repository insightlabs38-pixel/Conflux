// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { WebhooksPanel } from "./WebhooksPanel";

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
  throw new Error("Webhooks panel did not update");
}

it("shows scoped subscriptions and replays a failed delivery", async () => {
  const items = [
    {
      public_id: "s1",
      url: "https://receiver.example/hook",
      event_types: ["event.status_changed"],
      event: "e1",
      enabled: true,
    },
  ];
  const deliveries = [
    {
      public_id: "d1",
      event_id: "x1",
      event_type: "event.status_changed",
      status: "dead",
      attempts: 5,
      last_status_code: 503,
      last_error: "HTTP 503",
      next_attempt_at: null,
      created_at: "2026-09-27T00:00:00Z",
    },
  ];
  const fetchMock = vi
    .fn()
    .mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("replay/")) {
        deliveries[0].status = "pending";
        return { ok: true, json: async () => ({ ...deliveries[0] }) };
      }
      if (url.endsWith("deliveries/"))
        return {
          ok: true,
          json: async () => deliveries.map((row) => ({ ...row })),
        };
      if (init?.method === "POST")
        return {
          ok: true,
          json: async () => ({ ...items[0], secret: "one-time-secret" }),
        };
      return { ok: true, json: async () => items };
    });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<WebhooksPanel workspaceId="w1" eventId="e1" />));
  await until(
    () => container.textContent?.includes("receiver.example") ?? false,
  );
  const buttons = () => Array.from(container.querySelectorAll("button"));
  await act(async () =>
    buttons()
      .find((button) => button.textContent === "Delivery history")!
      .click(),
  );
  await until(() => container.textContent?.includes("HTTP 503") ?? false);
  await act(async () =>
    buttons()
      .find((button) => button.textContent === "Replay")!
      .click(),
  );
  await until(() => container.textContent?.includes("pending") ?? false);
  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining("d1/replay/"),
    expect.objectContaining({ method: "POST", credentials: "include" }),
  );
  act(() => root.unmount());
  container.remove();
});
