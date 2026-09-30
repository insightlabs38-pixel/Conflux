// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import { ConfigurationPanel } from "./ConfigurationPanel";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const entry = (over: Record<string, unknown>) => ({
  key: "registration.mode",
  module: "core",
  tier: "base",
  label: "Registration",
  help: "How people join.",
  value: "open",
  default: "open",
  baseline: "open",
  source: "preset",
  editable: true,
  lock: null,
  module_enabled: true,
  ...over,
});
const config = (settings: unknown[]) => ({
  event: "e1",
  preset: { key: "hackathon", version: 1, label: "Hackathon" },
  settings,
});

async function mount(respond: (url: string) => Response) {
  const fetchMock = vi.fn(async (input: unknown) => respond(String(input)));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(withQuery(<ConfigurationPanel workspaceId="w" eventId="e1" />)),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, fetchMock, root };
}

describe("ConfigurationPanel", () => {
  it("shows each value with where it comes from, what it started as, locks and modules that are off", async () => {
    const { container, root } = await mount(() =>
      jsonResponse(
        200,
        config([
          entry({}),
          entry({
            key: "registration.waitlist_enabled",
            label: "Waitlist",
            value: true,
            default: false,
            baseline: null,
            source: "overridden",
          }),
          entry({
            key: "event.starts_at",
            label: "Start",
            value: "2027-03-05T09:00:00Z",
            source: "set",
            lock: {
              code: "event_archived",
              message: "Archived event configuration cannot be edited.",
            },
          }),
          entry({
            key: "eligibility.require_clearance",
            label: "Require clearance",
            module: "eligibility_review",
            module_enabled: false,
            value: false,
            source: "default",
          }),
        ]),
      ),
    );
    const text = container.textContent ?? "";
    expect(text).toContain("this event started from the Hackathon format");
    expect(text).toContain("Registration: open");
    expect(text).toContain("From the format");
    expect(text).toContain("Waitlist: On");
    expect(text).toContain("Changed");
    expect(text).toContain("Started as Off.");
    expect(text).toContain("Start: Mar 5, 2027, 9:00 AM UTC");
    expect(text).toContain(
      "Locked: Archived event configuration cannot be edited.",
    );
    expect(text).toContain("Belongs to eligibility review, which is off.");
    act(() => root.unmount());
  });

  it("asks the server for the chosen source rather than filtering by itself", async () => {
    const { container, fetchMock, root } = await mount((url) =>
      jsonResponse(
        200,
        config(url.includes("source=overridden") ? [] : [entry({})]),
      ),
    );
    const select = container.querySelector("select")!;
    await act(async () => {
      select.value = "overridden";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
    const urls = fetchMock.mock.calls.map(([url]) => String(url));
    expect(urls[0]).toMatch(/\/configuration\/$/);
    expect(urls.at(-1)).toMatch(/\/configuration\/\?source=overridden$/);
    expect(container.textContent).toContain("No settings match.");
    act(() => root.unmount());
  });

  it("shows a failure with Try again", async () => {
    const { container, root } = await mount(() =>
      jsonResponse(503, { detail: "down" }),
    );
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
    expect(container.textContent).toContain("Try again");
    act(() => root.unmount());
  });
});
