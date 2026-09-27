// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EventTemplatesPanel } from "./EventTemplatesPanel";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

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

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Event templates panel did not update");
}

describe("EventTemplatesPanel", () => {
  it("saves a template from a source event and lists it", async () => {
    const events = [{ public_id: "e1", name: "Regionals" }];
    const savedTemplate = {
      public_id: "t1",
      name: "Starter kit",
      source_event_name: "Regionals",
      sections: ["tracks"],
      created_at: "2026-09-27T00:00:00Z",
    };
    const fetchMock = vi.fn().mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/events/") && method === "GET") return { ok: true, json: async () => events };
      if (url.endsWith("event-templates/") && method === "GET") {
        return { ok: true, json: async () => [] };
      }
      if (url.endsWith("event-templates/") && method === "POST") {
        return { ok: true, json: async () => savedTemplate };
      }
      throw new Error(`Unexpected request: ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<EventTemplatesPanel workspaceId="w1" />));
    await until(() => container.querySelector('option[value="e1"]') !== null);

    await act(async () => {
      const select = container.querySelector<HTMLSelectElement>("#tpl-source")!;
      select.value = "e1";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await act(async () => {
      const nameInput = container.querySelector<HTMLInputElement>("#tpl-name")!;
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set?.call(
        nameInput,
        "Starter kit",
      );
      nameInput.dispatchEvent(new Event("input", { bubbles: true }));
    });
    const forms = container.querySelectorAll("form");
    await act(async () => {
      (forms[0] as HTMLFormElement).requestSubmit();
    });

    await until(() => container.textContent?.includes("Starter kit") ?? false);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("event-templates/"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("selects a cloned event without reloading the page", async () => {
    const onCreated = vi.fn();
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/events/") && (!init?.method || init.method === "GET")) {
        return { ok: true, json: async () => [{ public_id: "e1", name: "Regionals" }] };
      }
      if (url.endsWith("event-templates/")) return { ok: true, json: async () => [] };
      if (url.endsWith("/events/e1/clone/")) {
        return { ok: true, json: async () => ({ public_id: "e2", name: "Clone", slug: "clone" }) };
      }
      throw new Error(`Unexpected request: ${url}`);
    }));
    act(() => root.render(<EventTemplatesPanel workspaceId="w1" onCreated={onCreated} />));
    await until(() => container.querySelector('option[value="e1"]') !== null);
    const change = async (selector: string, value: string, eventName: string) => {
      await act(async () => {
        const element = container.querySelector<HTMLInputElement | HTMLSelectElement>(selector)!;
        Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element), "value")?.set?.call(element, value);
        element.dispatchEvent(new Event(eventName, { bubbles: true }));
      });
    };
    await change("#tpl-source", "e1", "change");
    await change("#clone-name", "Clone", "input");
    await change("#clone-slug", "clone", "input");
    await act(async () => container.querySelectorAll("form")[1].requestSubmit());
    await until(() => onCreated.mock.calls.length > 0);
    expect(onCreated).toHaveBeenCalledWith("e2");
    expect(container.textContent).toContain('Created event "Clone"');
    expect(container.textContent).not.toContain("Reload to see it");
  });
});
