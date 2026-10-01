// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OrganizerOverview } from "./OrganizerOverview";
import { jsonResponse } from "../../lib/test-http";
import { withRouter } from "../../lib/test-router";

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

const READINESS = {
  data: null,
  error: null,
  loading: false,
  reload: async () => {},
  update: () => {},
};

async function mount(timeline: unknown) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      urls.push(String(url));
      return String(url).includes("/timeline/")
        ? jsonResponse(200, timeline)
        : jsonResponse(200, []);
    }),
  );
  await act(async () =>
    root.render(
      withRouter(
        <OrganizerOverview
          workspaceId="w"
          eventId="e1"
          starts={null}
          ends={null}
          status="open"
          readiness={READINESS}
        />,
      ),
    ),
  );
  await act(async () => new Promise((r) => setTimeout(r, 10)));
  return urls;
}

describe("OrganizerOverview coming up", () => {
  it("lists what is coming up in the event's clock and counts conflicts among it", async () => {
    const urls = await mount({
      event: "e1",
      timezone: "America/New_York",
      total: 2,
      items: [
        {
          key: "agenda:1",
          label: "Opening",
          local_starts_at: "2027-03-06T10:00:00-05:00",
          local_ends_at: "2027-03-06T11:00:00-05:00",
        },
        {
          key: "gate:1",
          label: "Submissions close",
          local_starts_at: "2027-03-07T09:00:00-05:00",
          local_ends_at: null,
        },
      ],
      conflicts: [
        {
          code: "outside_event",
          severity: "advisory",
          message: "x",
          items: ["agenda:1"],
        },
      ],
    });
    const request = urls.find((u) => u.includes("/timeline/"))!;
    expect(request).toMatch(/timeline\/\?from=.+&limit=5$/);
    const card = container.querySelector('[aria-label="Coming up"]')!;
    expect(card.textContent).toContain("Saturday, March 6 10:00–11:00");
    expect(card.textContent).toContain("Opening");
    expect(card.textContent).toContain("Sunday, March 7 09:00");
    expect(card.textContent).toContain("Open the timeline");
    expect(
      container.querySelector('[aria-label="Needs action"]')!.textContent,
    ).toContain("1 scheduling conflict among what is coming up");
  });

  it("says so when nothing is scheduled and raises no conflict", async () => {
    await mount({
      event: "e1",
      timezone: "UTC",
      total: 0,
      items: [],
      conflicts: [],
    });
    const card = container.querySelector('[aria-label="Coming up"]')!;
    expect(card.textContent).toContain("Nothing else is scheduled.");
    expect(
      container.querySelector('[aria-label="Needs action"]')!.textContent,
    ).not.toContain("scheduling conflict");
  });
});
