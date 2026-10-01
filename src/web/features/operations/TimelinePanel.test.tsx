// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TimelinePanel } from "./TimelinePanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import type { Timeline, TimelineItem } from "../../lib/timeline";

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
const timeline = (over: Partial<Timeline> = {}): Timeline => ({
  event: "e1",
  timezone: "America/New_York",
  total: 3,
  items: [
    item({
      kind: "gate",
      kind_label: "Registration and submission windows",
      key: "gate:1",
      label: "Registration",
      starts_at: "2027-03-01T12:00:00Z",
      ends_at: "2027-03-05T12:00:00Z",
      local_starts_at: "2027-03-01T07:00:00-05:00",
      local_ends_at: "2027-03-05T07:00:00-05:00",
    }),
    item(),
    item({
      key: "agenda:2",
      label: "Workshop",
      starts_at: "2027-03-06T16:00:00Z",
      ends_at: "2027-03-06T17:00:00Z",
      local_starts_at: "2027-03-06T11:00:00-05:00",
      local_ends_at: "2027-03-06T12:00:00-05:00",
      editable: false,
      write: null,
      note: "Not on the public agenda.",
    }),
  ],
  conflicts: [
    {
      code: "location_overlap",
      severity: "advisory",
      message: "Opening and Workshop overlap on the same location.",
      items: ["agenda:1", "agenda:2"],
    },
  ],
  ...over,
});

type Call = { url: string; method: string; body?: unknown };
async function mount(route: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call = {
        url: String(url),
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      return route(call);
    }),
  );
  await act(async () =>
    root.render(withQuery(<TimelinePanel workspaceId="w" eventId="e1" />)),
  );
  await settle();
  return calls;
}
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const button = (label: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === label || b.getAttribute("aria-label") === label,
  ) as HTMLButtonElement;
async function type(input: HTMLInputElement, value: string) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

describe("TimelinePanel", () => {
  it("groups the items by day in the event's clock and flags the conflicts", async () => {
    await mount(() => jsonResponse(200, timeline()));
    expect(container.textContent).toContain("America/New_York");
    const days = [...container.querySelectorAll("h4")].map(
      (h) => h.textContent,
    );
    expect(days).toEqual([
      "Worth a look",
      "Monday, March 1",
      "Saturday, March 6",
    ]);
    const march6 = container.querySelector('[aria-label="Saturday, March 6"]')!;
    expect(march6.textContent).toContain("10:00–11:30");
    expect(march6.textContent).toContain("Opening");
    expect(march6.textContent).toContain("Not on the public agenda.");
    expect(march6.querySelectorAll(".cx-badge--warning")).toHaveLength(2);
    expect(
      container.querySelector('[aria-label="Scheduling conflicts"]')!
        .textContent,
    ).toContain("Opening and Workshop overlap on the same location.");
    expect(container.textContent).toContain("nothing is blocked");
    expect(container.textContent).toContain("Mar" /* multi-day window */);
  });

  it("changes the times through the item's own write, in the event's zone", async () => {
    const calls = await mount((call) =>
      call.method === "PATCH"
        ? jsonResponse(200, {})
        : jsonResponse(200, timeline()),
    );
    expect(button("Change the times of Workshop")).toBeUndefined(); // no domain write
    await act(async () => button("Change the times of Opening").click());
    const form = container.querySelector(
      'form[aria-label="Times of Opening"]',
    )!;
    const [starts, ends] = [...form.querySelectorAll("input")];
    expect(starts.value).toBe("2027-03-06T10:00"); // the event's wall clock, not the viewer's
    await type(starts, "2027-03-06T10:30");
    await type(ends, "2027-03-06T12:00");
    await act(async () => button("Save").click());
    await settle();
    const patch = calls.find((c) => c.method === "PATCH")!;
    expect(patch.url).toBe("/api/v1/workspaces/w/events/e1/agenda/1/");
    expect(patch.body).toEqual({
      starts_at: "2027-03-06T15:30:00.000Z",
      ends_at: "2027-03-06T17:00:00.000Z",
    });
    expect(container.querySelector("form")).toBeNull(); // closed after saving
  });

  it("shows the domain's own refusal and keeps the form open", async () => {
    await mount((call) =>
      call.method === "PATCH"
        ? jsonResponse(400, { ends_at: ["Must be after starts_at."] })
        : jsonResponse(200, timeline()),
    );
    await act(async () => button("Change the times of Opening").click());
    await act(async () => button("Save").click());
    await settle();
    expect(container.querySelector("[role=alert]")!.textContent).toContain(
      "Must be after starts_at.",
    );
    expect(container.querySelector("form")).not.toBeNull();
    await act(async () => button("Cancel").click());
    expect(container.querySelector("form")).toBeNull();
  });

  it("filters by kind through the server", async () => {
    const calls = await mount(() => jsonResponse(200, timeline()));
    const box = [
      ...container.querySelectorAll<HTMLInputElement>("fieldset input"),
    ].find((i) =>
      i.parentElement!.textContent!.includes("Registration and submission"),
    )!;
    await act(async () => box.click()); // turn the windows off
    await settle();
    expect(calls.at(-1)!.url).toContain("kinds=agenda");
  });

  it("shows empty and failed states", async () => {
    await mount(() =>
      jsonResponse(200, timeline({ items: [], conflicts: [], total: 0 })),
    );
    expect(container.textContent).toContain("Nothing scheduled");
    act(() => root.unmount());
    root = createRoot(container);
    vi.unstubAllGlobals();
    await mount(() => jsonResponse(500, { detail: "Server error" }));
    expect(container.textContent).toContain("Server error");
    expect(button("Try again")).toBeDefined();
  });
});
