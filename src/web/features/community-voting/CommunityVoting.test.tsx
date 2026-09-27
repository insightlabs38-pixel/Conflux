// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CommunityVoting } from "./CommunityVoting";

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

async function waitFor(check: () => boolean, timeoutMs = 1000) {
  const start = Date.now();
  while (!check()) {
    if (Date.now() - start > timeoutMs) throw new Error("waitFor timed out");
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
}

describe("CommunityVoting", () => {
  it("renders nothing when the event has no voting plan", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => null }),
    );
    act(() => {
      root.render(<CommunityVoting eventId="e1" />);
    });
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(container.innerHTML).toBe("");
  });

  it("lists candidates and lets an authenticated voter cast one vote", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: unknown, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/status/")) {
          return {
            ok: true,
            status: 200,
            json: async () => ({ identity_mode: "authenticated", is_open: true }),
          };
        }
        if (url.includes("/candidates/")) {
          return {
            ok: true,
            status: 200,
            json: async () => [{ project: "p1", name: "Autograder" }],
          };
        }
        if (url.includes("/results/")) {
          return { ok: false, status: 403, json: async () => ({}) };
        }
        if (url.includes("/votes/") && init?.method === "POST") {
          return { ok: true, status: 201, json: async () => ({ public_id: "v1" }) };
        }
        return { ok: true, status: 200, json: async () => null };
      }),
    );
    act(() => {
      root.render(<CommunityVoting eventId="e1" />);
    });
    await waitFor(() => container.textContent?.includes("Autograder") ?? false);
    const voteButton = [...container.querySelectorAll("button")].find(
      (button) => button.textContent === "Vote",
    );
    act(() => {
      voteButton?.click();
    });
    await waitFor(() => container.textContent?.includes("voted") ?? false);
  });
});
