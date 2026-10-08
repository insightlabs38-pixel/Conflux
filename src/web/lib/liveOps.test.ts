import { describe, expect, it } from "vitest";
import { dataAge, describeHealth } from "./liveOps";
import { isLiveOpsTopic, liveOpsTopic } from "./realtime";

describe("live operations health", () => {
  it("says what each connection state means and only offline holds actions back", () => {
    expect(describeHealth("live", 15)).toMatchObject({
      tone: "ok",
      word: "Connected",
      blocksActions: false,
    });
    expect(describeHealth("polling", 15)).toMatchObject({
      tone: "degraded",
      blocksActions: false,
    });
    expect(describeHealth("polling", 15).detail).toContain("every 15 s");
    expect(describeHealth("connecting", 15).tone).toBe("degraded");
    const off = describeHealth("offline", 15);
    expect(off).toMatchObject({ tone: "offline", blocksActions: true });
    expect(off.detail).toContain("last data");
    expect(describeHealth("idle", 15).tone).toBe("idle");
  });

  it("shows the data's own time and its age, never a blank", () => {
    const at = new Date(2027, 2, 1, 14, 46, 20).getTime();
    expect(dataAge(at + 42_000, at)).toContain("14:46:20");
    expect(dataAge(at + 42_000, at)).toContain("42 s ago");
    expect(dataAge(at + 2_000, at)).toContain("just now");
    expect(dataAge(at + 5 * 60_000, at)).toContain("5 min ago");
    expect(dataAge(at + 3 * 3_600_000, at)).toContain("3 h ago");
    expect(dataAge(at - 5000, at)).toContain("just now"); // clock skew never reads negative
    expect(dataAge(at, null)).toBe("No data yet");
  });

  it("names the topic so that only live lists poll quickly", () => {
    const topic = liveOpsTopic("w", "e", "projects");
    expect(isLiveOpsTopic(topic)).toBe(true);
    expect(isLiveOpsTopic("workspace:w:inbox")).toBe(false);
  });
});
