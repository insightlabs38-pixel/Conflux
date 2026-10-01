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
  constraint: null,
  module_enabled: true,
  ...over,
});
const config = (settings: unknown[]) => ({
  event: "e1",
  preset: { key: "hackathon", version: 1, label: "Hackathon" },
  settings,
});

async function mount(respond: (url: string) => Response) {
  return mountWith((url) => respond(url));
}

async function mountWith(
  respond: (url: string, init?: RequestInit) => Response,
) {
  const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) =>
    respond(String(input), init),
  );
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
            key: "team.max_size",
            label: "Largest team",
            value: 5,
            source: "preset",
            constraint: "Between 1 and 100, and not below the smallest team.",
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
    // A constraint says what a valid new value must satisfy; a lock takes its place when present.
    expect(text).toContain(
      "Rule: Between 1 and 100, and not below the smallest team.",
    );
    expect(text).not.toContain("Rule: Archived");
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

  describe("changing a setting", () => {
    const write = (field: string, over = {}) => ({
      method: "PATCH",
      path: "workspaces/{workspace}/events/{event}/registration-settings/",
      field,
      body: "partial",
      ...over,
    });
    const mode = entry({
      schema: { type: "string", enum: ["open", "application", "invite_only"] },
      write: write("mode", { method: "PUT" }),
    });
    const maxSize = entry({
      key: "team.max_size",
      label: "Largest team",
      value: 5,
      schema: { type: ["integer", "null"], minimum: 1, maximum: 100 },
      write: write("max_size"),
    });
    const button = (container: HTMLElement, label: string) =>
      [...container.querySelectorAll("button")].find(
        (b) =>
          b.textContent === label || b.getAttribute("aria-label") === label,
      ) as HTMLButtonElement | undefined;
    const settle = () =>
      act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
    async function set(el: HTMLElement, value: string) {
      await act(async () => {
        const input = el as HTMLInputElement;
        const proto =
          el instanceof HTMLSelectElement
            ? HTMLSelectElement.prototype
            : HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, "value")!.set!.call(
          input,
          value,
        );
        el.dispatchEvent(
          new Event(el instanceof HTMLSelectElement ? "change" : "input", {
            bubbles: true,
          }),
        );
      });
    }

    it("saves through the endpoint the answer names and reloads what the server now says", async () => {
      let value = "open";
      const sent: { url: string; method: string; body: unknown }[] = [];
      const { container, root } = await mountWith((url, init) => {
        if (init?.method && init.method !== "GET") {
          sent.push({
            url,
            method: init.method,
            body: JSON.parse(String(init.body)),
          });
          value = (sent.at(-1)!.body as { mode: string }).mode;
          return jsonResponse(200, {});
        }
        return jsonResponse(200, config([{ ...mode, value }]));
      });
      await act(async () => button(container, "Change Registration")!.click());
      const select = container.querySelector(
        'form[aria-label="Change Registration"] select',
      ) as HTMLSelectElement;
      await set(select, "invite_only");
      await act(async () => button(container, "Save")!.click());
      await settle();
      expect(sent).toEqual([
        {
          url: "/api/v1/workspaces/w/events/e1/registration-settings/",
          method: "PUT",
          body: { mode: "invite_only" },
        },
      ]);
      expect(container.querySelector("form")).toBeNull();
      expect(container.textContent).toContain("Registration: invite only");
      act(() => root.unmount());
    });

    it("reads an endpoint that replaces everything first and sends the one field changed", async () => {
      const sent: { method: string; body: unknown }[] = [];
      const rules = entry({
        key: "eligibility.require_track",
        label: "Require a track",
        value: false,
        schema: { type: "boolean" },
        write: write("require_track", {
          method: "PUT",
          path: "workspaces/{workspace}/events/{event}/eligibility-rules/",
          body: "whole",
        }),
      });
      const { container, root } = await mountWith((url, init) => {
        if (init?.method === "PUT") {
          sent.push({ method: "PUT", body: JSON.parse(String(init.body)) });
          return jsonResponse(200, {});
        }
        if (url.endsWith("eligibility-rules/"))
          return jsonResponse(200, {
            require_track: false,
            require_clearance: true,
            updated_at: "x",
          });
        return jsonResponse(200, config([rules]));
      });
      await act(async () =>
        button(container, "Change Require a track")!.click(),
      );
      await act(async () =>
        (
          container.querySelector(
            'form input[type="checkbox"]',
          ) as HTMLInputElement
        ).click(),
      );
      await act(async () => button(container, "Save")!.click());
      await settle();
      expect(sent).toEqual([
        {
          method: "PUT",
          body: { require_track: true, require_clearance: true },
        },
      ]);
      act(() => root.unmount());
    });

    it("does not send a value the schema refuses, and shows the domain's own refusal", async () => {
      const sent: unknown[] = [];
      const { container, root } = await mountWith((_url, init) => {
        if (init?.method && init.method !== "GET") {
          sent.push(init.body);
          return jsonResponse(400, {
            max_size: ["Cannot be below the smallest team."],
          });
        }
        return jsonResponse(200, config([maxSize]));
      });
      await act(async () => button(container, "Change Largest team")!.click());
      const input = container.querySelector(
        'form input[type="number"]',
      ) as HTMLInputElement;
      await set(input, "500");
      expect(container.querySelector("[role=alert]")!.textContent).toContain(
        "from 1 to 100",
      );
      expect(button(container, "Save")!.disabled).toBe(true);
      await set(input, "3");
      await act(async () => button(container, "Save")!.click());
      await settle();
      expect(sent).toHaveLength(1);
      expect(
        container.querySelector("form [role=alert]")!.textContent,
      ).toContain("Cannot be below the smallest team.");
      expect(container.querySelector("form")).not.toBeNull(); // stays open for another try
      await act(async () => button(container, "Cancel")!.click());
      expect(container.querySelector("form")).toBeNull();
      act(() => root.unmount());
    });

    it("offers no change for a locked setting, a derived one or a module that is off", async () => {
      const { container, root } = await mountWith(() =>
        jsonResponse(
          200,
          config([
            {
              ...mode,
              editable: false,
              lock: { code: "event_archived", message: "Locked." },
            },
            {
              ...maxSize,
              key: "dates.duration_hours",
              write: null,
              editable: false,
            },
            {
              ...maxSize,
              key: "eligibility.require_clearance",
              module: "eligibility_review",
              module_enabled: false,
            },
          ]),
        ),
      );
      expect(container.textContent).not.toContain("Change");
      act(() => root.unmount());
    });
  });
});
