// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectForms } from "./ProjectForms";

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
  vi.unstubAllGlobals();
});

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Project form did not update");
}

async function change(
  element: HTMLInputElement | HTMLSelectElement,
  value: string,
) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      Object.getPrototypeOf(element),
      "value",
    )?.set?.call(element, value);
    element.dispatchEvent(
      new Event(element instanceof HTMLSelectElement ? "change" : "input", {
        bubbles: true,
      }),
    );
  });
}

describe("participant project forms", () => {
  it("loads saved answers and omits hidden conditional answers when saving", async () => {
    const form = {
      public_id: "v1",
      name: "Submission",
      number: 2,
      schema: {
        fields: [
          {
            id: "kind",
            type: "select",
            label: "Kind",
            options: ["Other", "AI"],
          },
          {
            id: "details",
            type: "text",
            label: "AI details",
            visible_if: { field: "kind", equals: "AI" },
          },
        ],
      },
    };
    const fetchMock = vi
      .fn()
      .mockImplementation(async (url: unknown, options?: RequestInit) => {
        const path = String(url);
        if (path.endsWith("/forms/"))
          return { ok: true, json: async () => [form] };
        if (path.endsWith("/artifacts/"))
          return { ok: true, json: async () => [] };
        if (options?.method === "PUT")
          return {
            ok: true,
            json: async () => ({
              answers: JSON.parse(String(options.body)).answers,
            }),
          };
        return {
          ok: true,
          json: async () => ({ answers: { kind: "AI", details: "Old" } }),
        };
      });
    vi.stubGlobal("fetch", fetchMock);
    act(() =>
      root.render(<ProjectForms workspaceId="w" eventId="e" projectId="p" />),
    );
    await waitFor(() => container.textContent?.includes("AI details") ?? false);
    expect(
      container.querySelector<HTMLInputElement>('input[value="Old"]'),
    ).not.toBeNull();
    await change(container.querySelector("select")!, "Other");
    expect(container.textContent).not.toContain("AI details");
    await act(async () => container.querySelector("form")!.requestSubmit());
    await waitFor(
      () => container.textContent?.includes("Answers saved") ?? false,
    );
    const put = fetchMock.mock.calls.find(
      ([, options]) => options?.method === "PUT",
    );
    expect(put).toBeDefined();
    expect(JSON.parse(String(put?.[1].body)).answers).toEqual({
      kind: "Other",
    });
  });

  it("keeps entered answers and reports an API rejection", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation(async (url: unknown, options?: RequestInit) => {
          const path = String(url);
          if (path.endsWith("/forms/"))
            return {
              ok: true,
              json: async () => [
                {
                  public_id: "v1",
                  name: "Submission",
                  number: 1,
                  schema: {
                    fields: [{ id: "pitch", type: "text", label: "Pitch" }],
                  },
                },
              ],
            };
          if (path.endsWith("/artifacts/"))
            return { ok: true, json: async () => [] };
          if (options?.method === "PUT")
            return {
              ok: false,
              status: 400,
              json: async () => ({ detail: "Rejected" }),
            };
          return { ok: true, json: async () => ({ answers: {} }) };
        }),
    );
    act(() =>
      root.render(<ProjectForms workspaceId="w" eventId="e" projectId="p" />),
    );
    await waitFor(() => container.querySelector("input") !== null);
    await change(container.querySelector("input")!, "My pitch");
    await act(async () => container.querySelector("form")!.requestSubmit());
    await waitFor(() => container.textContent?.includes("Rejected") ?? false);
    expect(container.querySelector<HTMLInputElement>("input")!.value).toBe(
      "My pitch",
    );
    expect(container.textContent).toContain("Unsaved answers");
  });
});
