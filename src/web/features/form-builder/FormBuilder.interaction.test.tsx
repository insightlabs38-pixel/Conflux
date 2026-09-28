// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { FormBuilder } from "./FormBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Timed out waiting for form UI");
}

describe("form builder preview", () => {
  it("shows a conditional field only when its choice matches", async () => {
    const form = {
      public_id: "f1",
      name: "Application",
      draft_schema: {
        fields: [
          {
            id: "kind",
            label: "Kind",
            type: "select",
            required: true,
            visible_to: ["participant"],
            options: ["build", "research"],
          },
          {
            id: "demo",
            label: "Demo",
            type: "url",
            required: false,
            visible_to: ["participant"],
            visible_if: { field: "kind", equals: "build" },
          },
        ],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (url: string) => ({
        ok: true,
        status: 200,
        json: async () => (String(url).endsWith("versions/") ? [] : [form]),
      })),
    );
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () => {
      root.render(<FormBuilder workspaceId="w" eventId="e" />);
    });
    await waitFor(() => container.querySelector("select") !== null);
    const formSelect = container.querySelector("select") as HTMLSelectElement;
    await act(async () => {
      formSelect.value = "f1";
      formSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await waitFor(
      () => container.querySelector('[aria-label="Form preview"]') !== null,
    );
    const preview = container.querySelector(
      '[aria-label="Form preview"]',
    ) as HTMLElement;
    expect(preview.textContent).toContain("Kind");
    expect(preview.textContent).not.toContain("Demo");
    const kindSelect = preview.querySelector("select") as HTMLSelectElement;
    await act(async () => {
      kindSelect.value = "build";
      kindSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(preview.textContent).toContain("Demo");
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});

it("restores a published form to draft without publishing", async () => {
  const schema = {
    fields: [
      {
        id: "pitch",
        label: "Restored pitch",
        type: "text",
        required: false,
        visible_to: ["participant"],
      },
    ],
  };
  const form = {
    public_id: "f1",
    name: "Application",
    draft_schema: { fields: [] },
  };
  const fetchMock = vi.fn().mockImplementation(async (url: string) => ({
    ok: true,
    status: 200,
    json: async () =>
      url.endsWith("restore/")
        ? { ...form, draft_schema: schema }
        : url.endsWith("versions/")
          ? [{ public_id: "v1", number: 1, schema }]
          : [form],
  }));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(<FormBuilder workspaceId="w" eventId="e" />),
  );
  await waitFor(() => container.querySelector("select") !== null);
  await act(async () => {
    const select = container.querySelector("select")!;
    select.value = "f1";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await waitFor(
    () => container.textContent?.includes("Restore to draft") ?? false,
  );
  await act(async () =>
    Array.from(container.querySelectorAll("button"))
      .find((b) => b.textContent === "Restore to draft")!
      .click(),
  );
  await waitFor(
    () => container.textContent?.includes("Publish to make it live") ?? false,
  );
  expect(container.textContent).toContain("Restored pitch");
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/workspaces/w/events/e/forms/f1/versions/v1/restore/",
    expect.objectContaining({ method: "POST" }),
  );
  expect(fetchMock.mock.calls.some(([url]) => url.endsWith("publish/"))).toBe(
    false,
  );
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});
