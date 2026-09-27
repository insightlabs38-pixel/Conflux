// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Inbox } from "./Inbox";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

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

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Inbox did not update");
}

describe("Inbox", () => {
  it("lists an unread message and marks it read", async () => {
    const message = {
      public_id: "r1",
      subject: "Reminder",
      body: "Submit soon.",
      event_name: "Demo Event",
      created_at: "2026-09-27T00:00:00Z",
      read_at: null,
    };
    const fetchMock = vi.fn().mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("read/")) {
        expect(init?.method).toBe("POST");
        return { ok: true, json: async () => ({ ...message, read_at: "2026-09-27T00:01:00Z" }) };
      }
      return { ok: true, json: async () => [message] };
    });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<Inbox workspaceId="w1" />));
    await until(() => container.textContent?.includes("Reminder") ?? false);
    expect(container.textContent).toContain("Submit soon.");
    expect(container.textContent).toContain("new");

    await act(async () => {
      container.querySelector("button")!.click();
    });
    await until(() => !(container.textContent?.includes("Mark read") ?? false));
    expect(container.textContent).not.toContain("new");
  });
});
