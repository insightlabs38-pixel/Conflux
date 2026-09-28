// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import ApiExplorer from "./ApiExplorer";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | undefined;
let container: HTMLDivElement;
afterEach(() => {
  if (root) act(() => root?.unmount());
  root = undefined;
  container?.remove();
  vi.unstubAllGlobals();
});
const path = "/api/v1/workspaces/{workspace_public_id}/events/";
const schema = {
  openapi: "3.0.3",
  paths: {
    "/api/v1/health/": { get: { operationId: "health" } },
    [path]: {
      post: {
        operationId: "create_event",
        parameters: [
          { in: "path", name: "workspace_public_id", required: true },
        ],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object" } } },
        },
      },
    },
  },
};

async function until(check: () => boolean) {
  for (let i = 0; i < 100; i++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Explorer did not update");
}
async function mount() {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
  await act(async () => root!.render(<ApiExplorer />));
}
async function click(label: string) {
  await act(async () =>
    Array.from(container.querySelectorAll("button"))
      .find((button) => button.textContent === label)!
      .click(),
  );
}
async function input(
  element: HTMLInputElement | HTMLTextAreaElement,
  value: string,
) {
  await act(async () => {
    const prototype =
      element instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(prototype, "value")?.set?.call(
      element,
      value,
    );
    element.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

it("seeds a write without sending, requires intent, and safely shows HTTP failures", async () => {
  const fetchMock = vi.fn(async (url: unknown) => {
    if (String(url).includes("schema/"))
      return { ok: true, json: async () => schema };
    return new Response('<script>alert("unsafe")</script>', {
      status: 403,
      headers: { "Content-Type": "text/html" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  await mount();
  await until(
    () => container.textContent?.includes("Create an example event") ?? false,
  );
  await click("Create an example event");
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const button = Array.from(container.querySelectorAll("button")).find(
    (button) => button.textContent === "Send request",
  )!;
  expect(button.disabled).toBe(true);
  expect(
    JSON.parse(
      (container.querySelector("textarea") as HTMLTextAreaElement).value,
    ),
  ).toMatchObject({ name: "API explorer demo" });
  await input(container.querySelector("input[required]")!, "w1");
  await act(async () =>
    (
      container.querySelector('input[type="checkbox"]') as HTMLInputElement
    ).click(),
  );
  await click("Send request");
  await until(() => container.textContent?.includes("HTTP 403") ?? false);
  expect(fetchMock).toHaveBeenLastCalledWith(
    "/api/v1/workspaces/w1/events/",
    expect.objectContaining({
      method: "POST",
      credentials: "include",
      redirect: "error",
    }),
  );
  expect(container.querySelector("script")).toBeNull();
  expect(container.textContent).toContain('<script>alert("unsafe")</script>');
  expect(button.disabled).toBe(true);
});

it("rejects invalid JSON before sending and uses bearer without a cookie", async () => {
  const fetchMock = vi.fn(async (url: unknown) =>
    String(url).includes("schema/")
      ? { ok: true, json: async () => schema }
      : new Response("{}", { status: 201 }),
  );
  vi.stubGlobal("fetch", fetchMock);
  await mount();
  await until(
    () => container.textContent?.includes("Create an example event") ?? false,
  );
  await click("Create an example event");
  await input(container.querySelector("input[required]")!, "w1");
  await input(container.querySelector("textarea")!, "not JSON");
  await act(async () =>
    (
      container.querySelector('input[type="checkbox"]') as HTMLInputElement
    ).click(),
  );
  await click("Send request");
  await until(() => container.querySelector('[role="alert"]') !== null);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  await input(container.querySelector("textarea")!, '{"name":"Example"}');
  const auth = container.querySelector("form select") as HTMLSelectElement;
  await act(async () => {
    auth.value = "bearer";
    auth.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await input(
    container.querySelector('input[type="password"]')!,
    "test-bearer",
  );
  await act(async () =>
    (
      container.querySelector('input[type="checkbox"]') as HTMLInputElement
    ).click(),
  );
  await click("Send request");
  await until(() => container.textContent?.includes("HTTP 201") ?? false);
  expect(fetchMock).toHaveBeenLastCalledWith(
    "/api/v1/workspaces/w1/events/",
    expect.objectContaining({
      credentials: "omit",
      headers: {
        Authorization: "Bearer test-bearer",
        "Content-Type": "application/json",
      },
    }),
  );
});

it("retries schema loading, searches operations and sends a seeded read", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 503 })
    .mockResolvedValueOnce({ ok: true, json: async () => schema })
    .mockResolvedValueOnce(new Response('{"status":"ok"}'));
  vi.stubGlobal("fetch", fetchMock);
  await mount();
  await until(() => container.textContent?.includes("503") ?? false);
  await click("Try again");
  await until(
    () => container.textContent?.includes("Check service health") ?? false,
  );
  await input(container.querySelector("input")!, "health");
  expect(container.textContent).toContain("1 matching operations");
  await click("Check service health");
  expect(fetchMock).toHaveBeenCalledTimes(2);
  await click("Send request");
  await until(() => container.textContent?.includes("HTTP 200") ?? false);
  expect(fetchMock).toHaveBeenLastCalledWith(
    "/api/v1/health/",
    expect.objectContaining({ method: "GET" }),
  );
});
