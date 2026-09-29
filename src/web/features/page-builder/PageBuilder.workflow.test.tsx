// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { PageBuilder } from "./PageBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Page builder did not update");
}

const button = (root: HTMLElement, label: string) =>
  [...root.querySelectorAll("button")].find(
    (b) => b.textContent?.trim() === label,
  ) as HTMLButtonElement | undefined;

it("selects one block to edit, reorders safely and confirms removal", async () => {
  const calls: { url: string; method: string }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      calls.push({ url, method });
      const body = url.endsWith("accessibility-audit/")
        ? []
        : url.endsWith("/blocks/")
          ? [
              {
                public_id: "b1",
                kind: "hero",
                position: 0,
                config: {
                  title: "First",
                  subtitle: "",
                  cta_label: "Go",
                  cta_link: "x/",
                },
              },
              {
                public_id: "b2",
                kind: "cta",
                position: 1,
                config: { label: "Join", link: "x/" },
              },
            ]
          : { public_id: "p1", theme: "default" };
      return {
        ok: true,
        status: method === "DELETE" ? 204 : 200,
        json: async () => body,
      };
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(<PageBuilder workspaceId="w" eventId="e" />),
  );
  await until(
    () => container.querySelector('[aria-label="Page blocks"]') !== null,
  );
  const items = container.querySelectorAll('[aria-label="Page blocks"] li');
  expect(items).toHaveLength(2);
  expect(container.textContent).toContain(
    "Unsaved changes".slice(0, 0) + "All changes saved",
  );
  expect(button(container, "Move up")?.disabled).toBe(true);
  // Removal needs an explicit second step.
  await act(async () => button(container, "Remove")!.click());
  expect(container.textContent).toContain(
    "Remove this block from the public page?",
  );
  expect(calls.some((c) => c.method === "DELETE")).toBe(false);
  await act(async () => button(container, "Keep block")!.click());
  expect(button(container, "Remove")).toBeTruthy();
  await act(async () => button(container, "Remove")!.click());
  await act(async () => button(container, "Confirm remove")!.click());
  await until(() => calls.some((c) => c.method === "DELETE"));
  expect(calls.find((c) => c.method === "DELETE")!.url).toContain(
    "/blocks/b1/",
  );
  // The preview link and task tabs exist.
  expect(container.querySelector('a[href="/e/e/"]')).not.toBeNull();
  expect(
    [...container.querySelectorAll('[role="tab"]')].map((t) => t.textContent),
  ).toEqual(expect.arrayContaining([expect.stringContaining("Appearance")]));
  act(() => root.unmount());
});
