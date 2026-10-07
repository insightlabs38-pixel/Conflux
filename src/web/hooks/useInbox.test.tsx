// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RealtimeProvider } from "./useRealtime";
import { useInbox } from "./useInbox";
import { RealtimeHub, manualTransport } from "../lib/realtime";
import { jsonResponse } from "../lib/test-http";
import { withQuery } from "../lib/test-router";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const make = (id: string, subject: string, read = false) => ({
  public_id: id,
  subject,
  body: "b",
  event_name: "Demo Event",
  created_at: "2026-09-27T00:00:00Z",
  read_at: read ? "2026-09-27T01:00:00Z" : null,
});

function Probe({ live }: { live?: boolean }) {
  const { messages, unread } = useInbox(
    "w1",
    live === undefined ? {} : { live },
  );
  return (
    <p>
      {unread} unread: {messages.map((m) => m.subject).join(",")}
    </p>
  );
}
async function until(check: () => boolean) {
  for (let i = 0; i < 100 && !check(); i++)
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
  expect(check()).toBe(true);
}

describe("useInbox", () => {
  it("refetches when a realtime hint arrives, showing exactly what the server returns", async () => {
    let rows = [make("r1", "First")];
    const fetchMock = vi.fn(async () => jsonResponse(200, rows));
    vi.stubGlobal("fetch", fetchMock);
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 0 });
    const container = document.createElement("div");
    document.body.appendChild(container);
    let root = createRoot(container);
    act(() =>
      root.render(
        withQuery(
          <RealtimeProvider hub={hub}>
            <Probe />
          </RealtimeProvider>,
        ),
      ),
    );
    await until(() => container.textContent?.includes("First") ?? false);
    expect(container.textContent).toContain("1 unread");
    expect(feed.openTopics()).toEqual(["workspace:w1:inbox"]);
    const before = fetchMock.mock.calls.length;
    rows = [make("r2", "Second"), make("r1", "First", true)];
    await act(async () => feed.emit("workspace:w1:inbox"));
    await until(() => container.textContent?.includes("Second") ?? false);
    expect(fetchMock.mock.calls.length).toBe(before + 1);
    expect(container.textContent).toContain("1 unread"); // r1 is now read
    act(() => root.unmount());
    expect(feed.openTopics()).toEqual([]); // closed with the screen
    root = createRoot(container);
    container.remove();
  });

  it("two instances share one query and one subscription's worth of reads", async () => {
    const rows = [make("r1", "First")];
    const fetchMock = vi.fn(async () => jsonResponse(200, rows));
    vi.stubGlobal("fetch", fetchMock);
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 0 });
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() =>
      root.render(
        withQuery(
          <RealtimeProvider hub={hub}>
            <Probe />
            <Probe live={false} />
          </RealtimeProvider>,
        ),
      ),
    );
    await until(() => (container.textContent ?? "").includes("First"));
    const before = fetchMock.mock.calls.length;
    await act(async () => feed.emit("workspace:w1:inbox"));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(fetchMock.mock.calls.length).toBe(before + 1); // one hint, one read
    expect(feed.openTopics()).toEqual(["workspace:w1:inbox"]);
    act(() => root.unmount());
    container.remove();
  });
});
