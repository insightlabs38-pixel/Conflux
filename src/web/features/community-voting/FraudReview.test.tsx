// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FraudReview } from "./FraudReview";

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
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 5)); });
  }
  throw new Error("Review did not update");
}

describe("FraudReview", () => {
  it("shows evidence and resolves a signal with an organizer note", async () => {
    const signal = {
      public_id: "signal-1", signal_type: "token_replay_attempt", detail: "A token was reused.",
      evidence: { state: "redeemed" }, occurred_at: "2026-09-27T00:00:00Z",
      resolved_at: null, resolution_note: "",
    };
    const fetchMock = vi.fn().mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const body = url.endsWith("resolve/") ? { ...signal, resolved_at: "2026-09-27T00:01:00Z", resolution_note: "Reviewed" } :
        url.endsWith("audit/") ? [{ public_id: "a1", actor: null, detail: "Suspicious voting activity detected", created_at: "2026-09-27T00:00:00Z" }] : [signal];
      expect(init?.credentials).toBe("include");
      return { ok: true, json: async () => body };
    });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<FraudReview workspaceId="w1" eventId="e1" />));
    await until(() => container.textContent?.includes("A token was reused.") ?? false);
    expect(container.textContent).toContain("redeemed");
    expect(container.textContent).toContain("Suspicious voting activity detected");
    const note = container.querySelector("textarea")!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set?.call(note, "Reviewed");
      note.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      container.querySelector("button")!.click();
    });
    await until(() => container.textContent?.includes("Resolved: Reviewed") ?? false);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("signal-1/resolve/"),
      expect.objectContaining({ method: "POST" }),
    );
  });
});
