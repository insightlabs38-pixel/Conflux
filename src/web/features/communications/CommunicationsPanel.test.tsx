// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CommunicationsPanel } from "./CommunicationsPanel";

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
  throw new Error("Communications panel did not update");
}

describe("CommunicationsPanel", () => {
  it("previews an audience and sends a message", async () => {
    const kinds = [{ key: "all_participants", label: "All participants", param_names: [], options: {} }];
    const sentMessage = {
      public_id: "m1",
      subject: "Welcome",
      body: "Hi",
      audience_kind: "all_participants",
      recipient_count: 2,
      email_failure_count: 0,
      created_at: "2026-09-27T00:00:00Z",
    };
    const fetchMock = vi.fn().mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("audiences/") && method === "GET") return { ok: true, json: async () => kinds };
      if (url.endsWith("messages/") && method === "GET") return { ok: true, json: async () => [] };
      if (url.endsWith("audiences/preview/")) return { ok: true, json: async () => ({ count: 2, sample: [{ username: "alice" }] }) };
      if (url.endsWith("messages/") && method === "POST") return { ok: true, json: async () => sentMessage };
      throw new Error(`Unexpected request: ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<CommunicationsPanel workspaceId="w1" eventId="e1" />));
    await until(() => container.querySelector("select") !== null);

    await act(async () => {
      container.querySelector<HTMLButtonElement>('button[type="button"]')!.click();
    });
    await until(() => container.textContent?.includes("2 recipient(s)") ?? false);
    expect(container.textContent).toContain("alice");

    await act(async () => {
      const subject = container.querySelector<HTMLInputElement>("#comms-subject")!;
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set?.call(subject, "Welcome");
      subject.dispatchEvent(new Event("input", { bubbles: true }));
      const body = container.querySelector<HTMLTextAreaElement>("#comms-body")!;
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set?.call(body, "Hi");
      body.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      container.querySelector("form")!.requestSubmit();
    });
    await until(() => container.textContent?.includes("Sent messages") && container.textContent?.includes("Welcome"));
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("communications/messages/"),
      expect.objectContaining({ method: "POST" }),
    );
  });
});
