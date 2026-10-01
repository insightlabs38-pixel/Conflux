import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "./test-http";
import {
  dayHeading,
  rangeText,
  saveTimes,
  timelineUrl,
  toLocalInput,
  wall,
  zonedToUtc,
  type TimelineItem,
} from "./timeline";

afterEach(() => vi.unstubAllGlobals());

const item = (over: Partial<TimelineItem> = {}): TimelineItem => ({
  kind: "agenda",
  kind_label: "Agenda",
  key: "agenda:1",
  label: "Opening",
  starts_at: "2027-03-06T15:00:00Z",
  ends_at: "2027-03-06T16:30:00Z",
  local_starts_at: "2027-03-06T10:00:00-05:00",
  local_ends_at: "2027-03-06T11:30:00-05:00",
  dst_note: null,
  source: {},
  editable: true,
  write: {
    method: "PATCH",
    path: "workspaces/{workspace}/events/{event}/agenda/1/",
    fields: { starts_at: "starts_at", ends_at: "ends_at" },
    extra: {},
  },
  note: "",
  ...over,
});

describe("timeline client", () => {
  it("builds the request from the chosen range, kinds and limit", () => {
    expect(timelineUrl("w", "e")).toBe(
      "/api/v1/workspaces/w/events/e/timeline/",
    );
    expect(
      timelineUrl("w", "e", {
        from: "2027-03-06T00:00:00Z",
        kinds: ["agenda", "gate"],
        limit: 5,
      }),
    ).toBe(
      "/api/v1/workspaces/w/events/e/timeline/?from=2027-03-06T00%3A00%3A00Z&kinds=agenda%2Cgate&limit=5",
    );
  });

  it("reads event wall times as written, whatever zone the viewer is in", () => {
    expect(wall("2027-03-06T10:00:00-05:00")).toEqual({
      date: "2027-03-06",
      time: "10:00",
    });
    expect(toLocalInput("2027-03-06T10:00:00-05:00")).toBe("2027-03-06T10:00");
    expect(dayHeading("2027-03-06")).toBe("Saturday, March 6");
    expect(rangeText(item())).toBe("10:00–11:30");
    expect(rangeText(item({ local_ends_at: null }))).toBe("10:00");
    expect(
      rangeText(
        item({
          local_starts_at: "2027-03-01T07:00:00-05:00",
          local_ends_at: "2027-03-05T07:00:00-05:00",
        }),
      ),
    ).toBe("March 1 07:00 – March 5 07:00");
  });

  it("turns a wall time in the event's zone into the right UTC instant", () => {
    const ny = "America/New_York";
    expect(zonedToUtc("2027-03-06T10:00", ny)).toBe("2027-03-06T15:00:00.000Z"); // EST
    expect(zonedToUtc("2027-03-20T10:00", ny)).toBe("2027-03-20T14:00:00.000Z"); // EDT
    expect(zonedToUtc("2027-03-06T10:00", "UTC")).toBe(
      "2027-03-06T10:00:00.000Z",
    );
    expect(zonedToUtc("2027-03-06T10:00", "Asia/Kolkata")).toBe(
      "2027-03-06T04:30:00.000Z",
    );
    // Clocks go forward 14 March 2027 at 02:00: 02:30 does not exist and lands after the gap.
    expect(zonedToUtc("2027-03-14T02:30", ny)).toBe("2027-03-14T07:30:00.000Z");
    // Clocks go back 7 November 2027: 01:30 happens twice; the first one is used.
    expect(zonedToUtc("2027-11-07T01:30", ny)).toBe("2027-11-07T05:30:00.000Z");
    expect(zonedToUtc("2027-11-07T03:30", ny)).toBe("2027-11-07T08:30:00.000Z");
  });

  it("sends new times to the domain endpoint the item names, with its extra fields", async () => {
    const calls: { url: string; method: string; body: unknown }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push({
          url: String(url),
          method: init?.method ?? "GET",
          body: JSON.parse(String(init?.body)),
        });
        return jsonResponse(200, {});
      }),
    );
    await saveTimes(
      "w",
      "e",
      item(),
      "2027-03-06T16:00:00.000Z",
      "2027-03-06T17:00:00.000Z",
    );
    expect(calls[0]).toEqual({
      url: "/api/v1/workspaces/w/events/e/agenda/1/",
      method: "PATCH",
      body: {
        starts_at: "2027-03-06T16:00:00.000Z",
        ends_at: "2027-03-06T17:00:00.000Z",
      },
    });
    const publication = item({
      write: {
        method: "PUT",
        path: "workspaces/{workspace}/events/{event}/publication-schedules/finalists/",
        fields: { starts_at: "opens_at", ends_at: "closes_at" },
        extra: { finalist_stage: "s1" },
      },
    });
    await saveTimes("w", "e", publication, "2027-03-08T20:00:00.000Z", null);
    expect(calls[1].body).toEqual({
      finalist_stage: "s1",
      opens_at: "2027-03-08T20:00:00.000Z",
    });
    expect(() => saveTimes("w", "e", item({ write: null }), "x", null)).toThrow(
      "cannot be changed here",
    );
  });
});
