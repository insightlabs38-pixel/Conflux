// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FormPreviewAs } from "./FormPreviewAs";
import { jsonResponse } from "../../lib/test-http";
import type { PreviewAs } from "../../lib/previewContext";

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

const V1 = {
  id: "v1",
  label: "Version 1",
  at: "2027-03-01T09:00:00Z",
  by: null,
  current: false,
};
const DRAFT = {
  id: "draft",
  label: "Current draft",
  at: null,
  by: null,
  current: true,
};
const row = (id: string, extra = {}) => ({
  id,
  label: id[0].toUpperCase() + id.slice(1),
  type: "text",
  required: false,
  required_if: null,
  visible_to: ["participant", "judge", "organizer"],
  visible_if: null,
  ...extra,
});
const answer = (over: Partial<PreviewAs<unknown>> = {}, data = {}) => ({
  surface: "form",
  label: "Application form",
  summary: "Previewing Version 1 (live). Nothing is saved or sent.",
  roles: ["participant", "judge", "organizer", "public"],
  versions: [V1, DRAFT],
  resolved: { role: null, at: null, version: V1, live: true },
  notices: [],
  data: {
    fields: [
      row("pitch", { required: true }),
      row("kind", { type: "select", options: ["a", "b"] }),
      row("track", {
        visible_if: { field: "kind", equals: "a" },
        required_if: { field: "kind", equals: "a" },
        visible_to: ["public", "organizer"],
      }),
    ],
    total: 3,
    hidden: 0,
    ...data,
  },
  ...over,
});

type Call = {
  url: string;
  body: { ref: unknown; context: unknown; input?: unknown };
};
async function mount(route: (call: Call) => Response, refreshKey = 0) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call = {
        url: String(url),
        body: JSON.parse(String(init?.body ?? "{}")),
      };
      calls.push(call);
      return route(call);
    }),
  );
  const render = (key: number) =>
    root.render(
      <FormPreviewAs workspaceId="w" eventId="e" formId="f" refreshKey={key} />,
    );
  await act(async () => render(refreshKey));
  await settle();
  return { calls, rerender: (key: number) => act(async () => render(key)) };
}
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
function choose(label: string, value: string) {
  const element = [...container.querySelectorAll("label")]
    .find((l) => l.textContent?.startsWith(label))!
    .querySelector("select")!;
  return act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLSelectElement.prototype,
      "value",
    )!.set!.call(element, value);
    element.dispatchEvent(new Event("change", { bubbles: true }));
  });
}

describe("FormPreviewAs", () => {
  it("asks for the live view first and lists the fields with their conditions in words", async () => {
    const { calls } = await mount(() => jsonResponse(200, answer()));
    expect(calls[0].url).toBe("/api/v1/workspaces/w/preview-as/form/");
    expect(calls[0].body).toEqual({
      ref: { event: "e", form: "f" },
      context: {},
    });
    const text = container.textContent!;
    expect(text).toContain(
      "Previewing Version 1 (live). Nothing is saved or sent.",
    );
    expect(text).toContain("Required");
    expect(text).toContain("When Kind is a");
    expect(text).toContain("Required when Kind is a");
    expect(container.querySelectorAll("tbody tr")).toHaveLength(3);
  });

  it("sends the chosen person and draws the answer, saying how many fields were hidden", async () => {
    const { calls } = await mount((call) =>
      (call.body.context as { role?: string }).role === "judge"
        ? jsonResponse(
            200,
            answer(
              {
                summary:
                  "Previewing as judge, Version 1 (live). Nothing is saved or sent.",
                resolved: { role: "judge", at: null, version: V1, live: true },
              },
              { fields: [row("pitch")], total: 3, hidden: 2 },
            ),
          )
        : jsonResponse(200, answer()),
    );
    await choose("Person", "judge");
    await settle();
    expect(calls.at(-1)!.body.context).toEqual({ role: "judge" });
    expect(container.textContent).toContain("Previewing as judge");
    expect(container.querySelectorAll("tbody tr")).toHaveLength(1);
    expect(container.textContent).toContain(
      "2 of 3 fields are not shown to that person.",
    );
  });

  it("shows the server's sentence for a time before any version, keeps the controls and the last list", async () => {
    await mount((call) =>
      (call.body.context as { at?: string }).at
        ? jsonResponse(400, {
            "context.at": [
              "Nothing was kept yet at that time; the first version was kept 2027-03-01T09:00:00Z.",
            ],
          })
        : jsonResponse(200, answer()),
    );
    const input = container.querySelector<HTMLInputElement>(
      'input[type="datetime-local"]',
    )!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )!.set!.call(input, "2027-01-01T00:00");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await settle();
    const alert = container.querySelector('[role="alert"]')!;
    expect(alert.textContent).toContain("Nothing was kept yet at that time");
    expect(alert.textContent).not.toContain("context.at");
    expect(container.querySelector("fieldset")).not.toBeNull();
    expect(container.querySelectorAll("tbody tr")).toHaveLength(3);
  });

  it("offers Try again when the first answer fails", async () => {
    let fail = true;
    const { calls } = await mount(() =>
      fail
        ? jsonResponse(404, { detail: "Not found." })
        : jsonResponse(200, answer()),
    );
    expect(container.querySelector('[role="alert"]')!.textContent).toContain(
      "Not found.",
    );
    fail = false;
    const retry = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Try again",
    )!;
    await act(async () => retry.click());
    await settle();
    expect(calls).toHaveLength(2);
    expect(container.querySelectorAll("tbody tr")).toHaveLength(3);
  });

  it("says when a version has no fields and when nobody of that kind would see any", async () => {
    await mount(() =>
      jsonResponse(200, answer({}, { fields: [], total: 0, hidden: 0 })),
    );
    expect(container.textContent).toContain("This version has no fields.");
    act(() => root.unmount());
    root = createRoot(container);
    await mount(() =>
      jsonResponse(200, answer({}, { fields: [], total: 2, hidden: 2 })),
    );
    expect(container.textContent).toContain(
      "None of this form's fields are shown to that person.",
    );
  });

  it("asks again when the form is saved or published", async () => {
    const { calls, rerender } = await mount(() => jsonResponse(200, answer()));
    await rerender(1);
    await settle();
    expect(calls).toHaveLength(2);
  });

  it("shows a notice such as an unpublished draft", async () => {
    await mount(() =>
      jsonResponse(
        200,
        answer({
          notices: [
            {
              code: "unpublished",
              message: "Nothing has been published yet; this is the draft.",
            },
          ],
        }),
      ),
    );
    expect(container.textContent).toContain("this is the draft");
  });
});
