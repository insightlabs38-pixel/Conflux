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
      platform: "generic",
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

it("sends the chosen delivery format when creating a subscription", async () => {
  const fetchMock = vi
    .fn()
    .mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") {
        expect(JSON.parse(String(init.body))).toMatchObject({
          platform: "discord",
        });
        return {
          ok: true,
          json: async () => ({
            public_id: "s2",
            url: "https://discord.com/api/webhooks/1/token",
            event_types: ["event.status_changed"],
            event: "e1",
            platform: "discord",
            enabled: true,
            secret: "one-time-secret",
          }),
        };
      }
      return { ok: true, json: async () => [] };
    });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<WebhooksPanel workspaceId="w1" eventId="e1" />));
  await until(() => container.querySelector("form") !== null);

  const urlInput = container.querySelector(
    'input[type="url"]',
  ) as HTMLInputElement;
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )?.set?.call(urlInput, "https://discord.com/api/webhooks/1/token");
    urlInput.dispatchEvent(new Event("input", { bubbles: true }));
  });
  const platformSelect = container.querySelector("select") as HTMLSelectElement;
  await act(async () => {
    platformSelect.value = "discord";
    platformSelect.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await act(async () => {
    (container.querySelector("form") as HTMLFormElement).requestSubmit();
  });

  await until(
    () => container.textContent?.includes("one-time-secret") ?? false,
  );
  act(() => root.unmount());
  container.remove();
});

it("inspects exact payloads, signed attempts and a changed replay destination", async () => {
  const subscription = {
    public_id: "s1",
    url: "https://receiver.example/hook",
    event_types: ["event.created"],
    event: "e1",
    platform: "generic",
    enabled: true,
  };
  const delivery = {
    public_id: "d1",
    event_id: "x1",
    event_type: "event.created",
    status: "dead",
    attempts: 5,
    last_status_code: 503,
    last_error: "HTTP 503",
    next_attempt_at: null,
    created_at: "2026-09-28T00:00:00Z",
  };
  const detail = {
    ...delivery,
    destination: subscription.url,
    next_body: '<script>alert("unsafe")</script>',
    body_sha256: "body-digest",
    signature_scheme: "v1=HMAC-SHA256",
    history_has_more: true,
    history: [
      {
        public_id: "a1",
        destination: subscription.url,
        body: "original body",
        headers: { "X-Conflux-Signature": "v1=original-signature" },
        started_at: delivery.created_at,
        completed_at: null,
        status_code: null,
        error: "",
      },
    ],
  };
  const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input);
    if (init?.method === "PATCH") {
      subscription.url = JSON.parse(String(init.body)).url;
      return { ok: true, json: async () => subscription };
    }
    if (url.includes("d1/?offset=")) {
      const older = url.endsWith("offset=1");
      return {
        ok: true,
        json: async () => ({
          ...detail,
          history_has_more: !older,
          history: older
            ? [{ ...detail.history[0], public_id: "a0", body: "older body" }]
            : detail.history,
        }),
      };
    }
    if (url.endsWith("deliveries/"))
      return { ok: true, json: async () => [delivery] };
    return { ok: true, json: async () => [subscription] };
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<WebhooksPanel workspaceId="w1" eventId="e1" />));
  const click = async (label: string) => {
    await act(async () =>
      Array.from(container.querySelectorAll("button"))
        .find((b) => b.textContent === label)!
        .click(),
    );
  };
  await until(
    () => container.textContent?.includes("receiver.example") ?? false,
  );
  await click("Delivery history");
  await until(() => container.textContent?.includes("HTTP 503") ?? false);
  await click("Inspect");
  await until(() => container.textContent?.includes("body-digest") ?? false);
  expect(container.textContent).toContain("v1=original-signature");
  expect(container.textContent).toContain("Outcome unknown");
  expect(container.textContent).toContain('<script>alert("unsafe")</script>');
  expect(container.querySelector("script")).toBeNull();
  await click("Load older attempts");
  await until(() => container.textContent?.includes("older body") ?? false);
  expect(container.textContent).toContain("original body");
  const input = container.querySelector(
    'section input[type="url"]',
  ) as HTMLInputElement;
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )?.set?.call(input, "https://new.example/hook");
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await act(async () =>
    (input.closest("form") as HTMLFormElement).requestSubmit(),
  );
  await until(() => container.textContent?.includes("new.example") ?? false);
  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining("s1/"),
    expect.objectContaining({
      method: "PATCH",
      body: JSON.stringify({ url: "https://new.example/hook" }),
      credentials: "include",
    }),
  );
  expect(
    container.querySelector('[aria-label="Webhook inspection"]'),
  ).toBeNull();
  act(() => root.unmount());
  container.remove();
});

it("shows inspection failures and hides replay for a disabled subscription", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const url = String(input);
      if (url.includes("d1/"))
        return {
          ok: false,
          status: 403,
          json: async () => ({ detail: "Access denied" }),
        };
      if (url.endsWith("deliveries/"))
        return {
          ok: true,
          json: async () => [
            {
              public_id: "d1",
              event_type: "event.created",
              status: "dead",
              attempts: 5,
              created_at: "2026-09-28T00:00:00Z",
            },
          ],
        };
      return {
        ok: true,
        json: async () => [
          {
            public_id: "s1",
            url: "https://receiver.example/",
            enabled: false,
            event: "e1",
            platform: "generic",
            event_types: ["event.created"],
          },
        ],
      };
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<WebhooksPanel workspaceId="w1" eventId="e1" />));
  await until(
    () => container.textContent?.includes("receiver.example") ?? false,
  );
  await act(async () =>
    Array.from(container.querySelectorAll("button"))
      .find((b) => b.textContent === "Delivery history")!
      .click(),
  );
  await until(() => container.textContent?.includes("dead") ?? false);
  expect(
    Array.from(container.querySelectorAll("button")).some(
      (b) => b.textContent === "Replay",
    ),
  ).toBe(false);
  await act(async () =>
    Array.from(container.querySelectorAll("button"))
      .find((b) => b.textContent === "Inspect")!
      .click(),
  );
  await until(() => container.querySelector('[role="alert"]') !== null);
  expect(container.querySelector('[role="alert"]')?.textContent).toBe(
    "Access denied",
  );
  act(() => root.unmount());
  container.remove();
});

it("discards inspection responses after switching subscriptions", async () => {
  let resolveInspection: (value: unknown) => void = () => {};
  const pending = new Promise((resolve) => {
    resolveInspection = resolve;
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const url = String(input);
      if (url.includes("d1/?")) return { ok: true, json: async () => pending };
      if (url.endsWith("deliveries/"))
        return {
          ok: true,
          json: async () => [
            {
              public_id: "d1",
              event_type: "event.created",
              status: "dead",
              attempts: 5,
              created_at: "2026-09-28T00:00:00Z",
            },
          ],
        };
      return {
        ok: true,
        json: async () =>
          ["s1", "s2"].map((id) => ({
            public_id: id,
            url: `https://${id}.example/`,
            enabled: true,
            event: "e1",
            platform: "generic",
            event_types: ["event.created"],
          })),
      };
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<WebhooksPanel workspaceId="w1" eventId="e1" />));
  const buttons = (label: string) =>
    Array.from(container.querySelectorAll("button")).filter(
      (b) => b.textContent === label,
    );
  await until(() => buttons("Delivery history").length === 2);
  await act(async () => buttons("Delivery history")[0].click());
  await until(() => buttons("Inspect").length === 1);
  await act(async () => buttons("Inspect")[0].click());
  await act(async () => buttons("Delivery history")[1].click());
  await act(async () =>
    resolveInspection({ next_body: "stale payload", history: [] }),
  );
  expect(
    container.querySelector('[aria-label="Webhook inspection"]'),
  ).toBeNull();
  expect(
    (container.querySelector('section input[type="url"]') as HTMLInputElement)
      .value,
  ).toBe("https://s2.example/");
  act(() => root.unmount());
  container.remove();
});
