// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NotificationPreferences } from "./NotificationPreferences";
import type { NotificationPreferences as Preferences } from "../../lib/notifications";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";

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

const channel = (over: object) => ({
  channel: "email",
  label: "Email",
  enabled: true,
  locked: false,
  default: true,
  chosen: false,
  ...over,
});
const inbox = channel({
  channel: "inbox",
  label: "In-app inbox",
  locked: true,
});
const list = (announcementEmail = true): Preferences => ({
  categories: [
    {
      category: "announcement",
      label: "Announcements and reminders",
      description: "From the organizers.",
      essential: false,
      channels: [
        inbox,
        channel({ enabled: announcementEmail, chosen: !announcementEmail }),
      ],
    },
    {
      category: "essential",
      label: "Account and safety notices",
      description: "Always delivered.",
      essential: true,
      channels: [{ ...inbox }, channel({ locked: true })],
    },
  ],
});
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
async function until(check: () => boolean) {
  for (let i = 0; i < 100 && !check(); i++)
    await act(async () => new Promise((r) => setTimeout(r, 10)));
  expect(check()).toBe(true);
}
const boxes = () => [
  ...container.querySelectorAll<HTMLInputElement>("input[type=checkbox]"),
];

async function mount(route: (method: string, body?: unknown) => Response) {
  const calls: { method: string; url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({ method, url: String(url), body });
      return route(method, body);
    }),
  );
  await act(async () =>
    root.render(withQuery(<NotificationPreferences workspaceId="w" />)),
  );
  await settle();
  return calls;
}

describe("NotificationPreferences", () => {
  it("shows every category and channel with fixed ones disabled and explained", async () => {
    await mount(() => jsonResponse(200, list()));
    await until(() => boxes().length === 4);
    expect(
      [...container.querySelectorAll("legend")].map((l) => l.textContent),
    ).toEqual(["Announcements and reminders", "Account and safety notices"]);
    expect(boxes().map((b) => [b.checked, b.disabled])).toEqual([
      [true, true], // inbox, always kept
      [true, false], // announcement email, the person's to change
      [true, true],
      [true, true], // essential email, always sent
    ]);
    expect(container.textContent).toContain("Always kept");
    expect(container.textContent).toContain("Always sent");
    expect(container.textContent).toContain("default");
  });

  it("saves a choice at once and shows what the server answered", async () => {
    const calls = await mount((method) =>
      jsonResponse(200, method === "PUT" ? list(false) : list()),
    );
    await until(() => boxes().length === 4);
    await act(async () => boxes()[1].click());
    await until(() => container.querySelector('[role="status"]') !== null);
    const put = calls.find((c) => c.method === "PUT")!;
    expect(put.url).toBe("/api/v1/workspaces/w/notification-preferences/");
    expect(put.body).toEqual({
      category: "announcement",
      channel: "email",
      enabled: false,
    });
    expect(boxes()[1].checked).toBe(false);
    expect(container.querySelector('[role="status"]')!.textContent).toBe(
      "Announcements and reminders: Email off.",
    );
    expect(container.textContent).not.toContain("· default");
  });

  it("keeps the old value and says why when the server refuses", async () => {
    await mount((method) =>
      method === "PUT"
        ? jsonResponse(400, {
            channel: ["Essential notices are always delivered."],
          })
        : jsonResponse(200, list()),
    );
    await until(() => boxes().length === 4);
    await act(async () => boxes()[1].click());
    await until(() => container.querySelector('[role="alert"]') !== null);
    expect(container.querySelector('[role="alert"]')!.textContent).toContain(
      "always delivered",
    );
    expect(boxes()[1].checked).toBe(true);
  });

  it("shows a load failure with a retry", async () => {
    let fail = true;
    await mount(() =>
      fail
        ? jsonResponse(500, { detail: "Server error." })
        : jsonResponse(200, list()),
    );
    await until(() => container.textContent!.includes("Try again"));
    fail = false;
    const retry = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Try again",
    )!;
    await act(async () => retry.click());
    await until(() => boxes().length === 4);
  });
});
