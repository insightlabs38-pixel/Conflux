// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  RealtimeProvider,
  useConnectionStatus,
  useRealtime,
  useRealtimeInvalidate,
} from "./useRealtime";
import { RealtimeHub, manualTransport } from "../lib/realtime";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});
const tick = () => act(async () => new Promise((r) => setTimeout(r, 5)));

function Live({ topic, enabled }: { topic: string; enabled?: boolean }) {
  const count = useQuery({
    queryKey: ["count"],
    queryFn: () => counter.next(),
  });
  useRealtimeInvalidate(topic, ["count"], enabled);
  const status = useConnectionStatus(topic);
  return (
    <p>
      {String(count.data)}|{status}
    </p>
  );
}
const counter = {
  value: 0,
  next() {
    return ++this.value;
  },
};

function setup(node: React.ReactElement, hub?: RealtimeHub) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const tree = (
    <QueryClientProvider client={client}>
      {hub ? <RealtimeProvider hub={hub}>{node}</RealtimeProvider> : node}
    </QueryClientProvider>
  );
  act(() => root.render(tree));
}

describe("realtime hooks", () => {
  beforeEach(() => {
    counter.value = 0;
  });

  it("a hint refetches the query and the status is exposed", async () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 0 });
    setup(<Live topic="t" />, hub);
    await tick();
    expect(container.textContent).toBe("1|live");
    await act(async () => feed.emit("t"));
    await tick();
    expect(container.textContent).toBe("2|live");
  });

  it("does nothing without a hub, and does not subscribe while disabled", async () => {
    setup(<Live topic="t" />);
    await tick();
    expect(container.textContent).toBe("1|idle");
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport);
    setup(<Live topic="t" enabled={false} />, hub);
    await tick();
    expect(feed.openTopics()).toEqual([]);
  });

  it("useRealtime calls the latest handler and unsubscribes on unmount", async () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 0 });
    const seen: string[] = [];
    function Probe({ label }: { label: string }) {
      useRealtime("t", () => seen.push(label));
      return null;
    }
    setup(<Probe label="a" />, hub);
    setup(<Probe label="b" />, hub);
    await act(async () => feed.emit("t"));
    await tick();
    expect(seen).toEqual(["b"]);
    act(() => root.unmount());
    expect(feed.openTopics()).toEqual([]);
    root = createRoot(container);
  });

  it("session reset closes subscriptions", () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport);
    setup(<Live topic="t" />, hub);
    expect(feed.openTopics()).toEqual(["t"]);
    act(() => hub.reset());
    expect(feed.openTopics()).toEqual([]);
    const spy = vi.fn();
    hub.subscribe("t", spy)();
  });
});
