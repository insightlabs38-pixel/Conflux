// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  manualTransport,
  pollingTransport,
  RealtimeHub,
  type ConnectionStatus,
} from "./realtime";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("RealtimeHub", () => {
  it("shares one transport subscription per topic and closes it with the last subscriber", () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport);
    const offA = hub.subscribe("workspace:w:inbox", () => {});
    const offB = hub.subscribe("workspace:w:inbox", () => {});
    hub.subscribe("workspace:w:other", () => {})();
    expect(feed.openTopics()).toEqual(["workspace:w:inbox"]);
    offA();
    expect(feed.openTopics()).toEqual(["workspace:w:inbox"]);
    offB();
    offB(); // idempotent
    expect(feed.openTopics()).toEqual([]);
    expect(hub.status("workspace:w:inbox")).toBe("idle");
  });

  it("coalesces a burst of hints into one handler call and delivers to every subscriber", () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 250 });
    const a = vi.fn();
    const b = vi.fn();
    hub.subscribe("t", a);
    hub.subscribe("t", b);
    for (let i = 0; i < 5; i++) feed.emit("t", `n${i}`);
    expect(a).not.toHaveBeenCalled();
    vi.advanceTimersByTime(250);
    expect(a).toHaveBeenCalledTimes(1);
    expect(a).toHaveBeenCalledWith({ topic: "t", kind: "n4" });
    expect(b).toHaveBeenCalledTimes(1);
    feed.emit("t");
    vi.advanceTimersByTime(250);
    expect(a).toHaveBeenCalledTimes(2);
  });

  it("isolates a failing handler from the others", () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 0 });
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const good = vi.fn();
    hub.subscribe("t", () => {
      throw new Error("boom");
    });
    hub.subscribe("t", good);
    feed.emit("t");
    vi.advanceTimersByTime(0);
    expect(good).toHaveBeenCalled();
    expect(errors).toHaveBeenCalled();
    errors.mockRestore();
  });

  it("reports connection status changes to listeners", () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport);
    const seen: ConnectionStatus[] = [];
    hub.onChange(() => seen.push(hub.status("t")));
    hub.subscribe("t", () => {});
    feed.setStatus("t", "polling");
    expect(hub.status("t")).toBe("polling");
    expect(seen).toContain("polling");
  });

  it("reset closes everything, drops pending hints, and later unsubscribes are safe", () => {
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport, { coalesceMs: 250 });
    const handler = vi.fn();
    const off = hub.subscribe("t", handler);
    feed.emit("t");
    hub.reset();
    vi.advanceTimersByTime(1000);
    expect(handler).not.toHaveBeenCalled();
    expect(feed.openTopics()).toEqual([]);
    expect(() => off()).not.toThrow();
  });
});

describe("pollingTransport", () => {
  const setVisibility = (state: "visible" | "hidden") =>
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => state,
    });
  afterEach(() => setVisibility("visible"));

  it("hints once per interval while visible, pauses when hidden and fires once on resume", () => {
    setVisibility("visible");
    const hub = new RealtimeHub(pollingTransport({ intervalMs: 1000 }), {
      coalesceMs: 0,
    });
    const handler = vi.fn();
    const off = hub.subscribe("t", handler);
    expect(hub.status("t")).toBe("polling");
    vi.advanceTimersByTime(3001); // the last hint's zero-delay flush runs in the extra tick
    expect(handler).toHaveBeenCalledTimes(3);
    setVisibility("hidden");
    vi.advanceTimersByTime(5000);
    expect(handler).toHaveBeenCalledTimes(3);
    setVisibility("visible");
    document.dispatchEvent(new Event("visibilitychange"));
    vi.advanceTimersByTime(0);
    expect(handler).toHaveBeenCalledTimes(4);
    off();
    vi.advanceTimersByTime(5000);
    expect(handler).toHaveBeenCalledTimes(4);
  });

  it("reports offline and does not hint while the browser is offline", () => {
    const hub = new RealtimeHub(pollingTransport({ intervalMs: 1000 }), {
      coalesceMs: 0,
    });
    const handler = vi.fn();
    hub.subscribe("t", handler);
    Object.defineProperty(navigator, "onLine", {
      configurable: true,
      value: false,
    });
    vi.advanceTimersByTime(2000);
    expect(hub.status("t")).toBe("offline");
    expect(handler).not.toHaveBeenCalled();
    Object.defineProperty(navigator, "onLine", {
      configurable: true,
      value: true,
    });
    window.dispatchEvent(new Event("online"));
    vi.advanceTimersByTime(0);
    expect(hub.status("t")).toBe("polling");
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
