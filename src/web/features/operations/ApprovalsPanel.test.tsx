// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApprovalsPanel } from "./ApprovalsPanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import type { Approval, Gate } from "../../lib/approvals";

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

const GATE: Gate = {
  action: "message_send",
  label: "Sending a message to an audience",
  description: "Another organizer confirms it first.",
  deciders: ["organizer", "admin"],
  min_approvals: 1,
  enabled: false,
};
const approval = (over: Partial<Approval> = {}): Approval => ({
  public_id: "a1",
  action: "message_send",
  label: "Sending a message to an audience",
  subject: null,
  summary: ["Send “Welcome” to 2 people.", "Audience: all participants."],
  status: "pending",
  requested_by: "org",
  required_approvals: 1,
  approvals: 0,
  decisions: [],
  expires_at: "2026-10-04T10:00:00Z",
  created_at: "2026-10-01T10:00:00Z",
  executed_at: null,
  can_decide: false,
  can_cancel: true,
  ...over,
});

type Call = { url: string; method: string; body?: unknown };
async function mount(route: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call = {
        url: String(url),
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      return route(call);
    }),
  );
  await act(async () =>
    root.render(withQuery(<ApprovalsPanel workspaceId="w" eventId="e1" />)),
  );
  await settle();
  return calls;
}
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const button = (text: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === text,
  )!;

describe("ApprovalsPanel", () => {
  it("lists the gates as off by default and switches one through the server", async () => {
    const calls = await mount((call) => {
      if (call.method === "PUT")
        return jsonResponse(200, { ...GATE, enabled: true });
      return call.url.includes("approval-gates")
        ? jsonResponse(200, [GATE])
        : jsonResponse(200, []);
    });
    const box = container.querySelector<HTMLInputElement>(
      "input[type=checkbox]",
    )!;
    expect(box.checked).toBe(false);
    expect(container.textContent).toContain("Off by default");
    expect(container.textContent).toContain("No approval requests");
    await act(async () => box.click());
    await settle();
    const put = calls.find((c) => c.method === "PUT")!;
    expect(put.url).toBe(
      "/api/v1/workspaces/w/events/e1/approval-gates/message_send/",
    );
    expect(put.body).toEqual({ enabled: true });
  });

  it("shows what is being approved and lets another person approve or reject with a note", async () => {
    const calls = await mount((call) => {
      if (call.method === "POST")
        return jsonResponse(200, approval({ status: "approved" }));
      return call.url.includes("approval-gates")
        ? jsonResponse(200, [GATE])
        : jsonResponse(200, [approval({ can_decide: true })]);
    });
    expect(container.textContent).toContain("Send “Welcome” to 2 people.");
    expect(container.textContent).toContain("Asked by org");
    const input = container.querySelector<HTMLInputElement>(
      'input[maxlength="500"]',
    )!;
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )!.set!;
      setter.call(input, "Looks right");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => button("Approve").click());
    await settle();
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toBe(
      "/api/v1/workspaces/w/events/e1/approvals/a1/decision/",
    );
    expect(post.body).toEqual({ decision: "approve", note: "Looks right" });
  });

  it("does not offer the asker their own approval, only a withdrawal and the reason", async () => {
    const calls = await mount((call) =>
      call.method === "POST"
        ? jsonResponse(200, approval({ status: "cancelled" }))
        : call.url.includes("approval-gates")
          ? jsonResponse(200, [GATE])
          : jsonResponse(200, [approval({ can_decide: false })]),
    );
    expect(container.textContent).toContain("Waiting for another person");
    expect(button("Approve")).toBeUndefined();
    await act(async () => button("Withdraw").click());
    await settle();
    expect(calls.find((c) => c.method === "POST")!.url).toContain(
      "/a1/cancel/",
    );
  });

  it("shows a refusal from the server and recovers on retry", async () => {
    let fail = true;
    await mount((call) => {
      if (call.url.includes("approval-gates")) return jsonResponse(200, [GATE]);
      return fail
        ? jsonResponse(500, { detail: "Server error" })
        : jsonResponse(200, []);
    });
    expect(container.textContent).toContain("Server error");
    fail = false;
    await act(async () => button("Try again").click());
    await settle();
    expect(container.textContent).toContain("No approval requests");
  });
});
