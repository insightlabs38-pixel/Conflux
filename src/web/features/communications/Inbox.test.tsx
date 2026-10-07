// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Inbox } from "./Inbox";
import { withQuery } from "../../lib/test-router";
import { RealtimeProvider } from "../../hooks/useRealtime";
import { RealtimeHub, manualTransport } from "../../lib/realtime";
import { jsonResponse } from "../../lib/test-http";

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
    const fetchMock = vi
      .fn()
      .mockImplementation(async (input: unknown, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("read/")) {
          expect(init?.method).toBe("POST");
          return {
            ok: true,
            json: async () => ({ ...message, read_at: "2026-09-27T00:01:00Z" }),
          };
        }
        return { ok: true, json: async () => [message] };
      });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(withQuery(<Inbox workspaceId="w1" />)));
    await until(() => container.textContent?.includes("Reminder") ?? false);
    expect(container.textContent).toContain("Submit soon.");
    expect(container.textContent).toContain("new");

    await act(async () => {
      container.querySelector("button")!.click();
    });
    await until(() => !(container.textContent?.includes("Mark read") ?? false));
    expect(container.textContent).not.toContain("new");
  });

  it("leaves the realtime topic to the header's notification center (a second subscriber would double the reads)", async () => {
    const make = (id: string, subject: string) => ({
      public_id: id,
      subject,
      body: "b",
      event_name: "Demo Event",
      created_at: "2026-09-27T00:00:00Z",
      read_at: null,
    });
    let rows = [make("r1", "First")];
    const fetchMock = vi.fn(async () => jsonResponse(200, rows));
    vi.stubGlobal("fetch", fetchMock);
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 0 });
    act(() =>
      root.render(
        withQuery(
          <RealtimeProvider hub={hub}>
            <Inbox workspaceId="w1" />
          </RealtimeProvider>,
        ),
      ),
    );
    await until(() => container.textContent?.includes("First") ?? false);
    expect(feed.openTopics()).toEqual([]);
    const before = fetchMock.mock.calls.length;
    rows = [make("r2", "Second"), make("r1", "First")];
    await act(async () => feed.emit("workspace:w1:inbox"));
    expect(fetchMock.mock.calls.length).toBe(before); // no hint is heard here
    act(() => root.unmount());
    root = createRoot(container);
  });
});
