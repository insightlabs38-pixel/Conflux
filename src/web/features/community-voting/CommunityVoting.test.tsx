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
      vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, json: async () => null }),
    );
    act(() => {
      root.render(<CommunityVoting eventId="e1" />);
    });
    await act(async () => new Promise((resolve) => setTimeout(resolve, 20)));
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
            json: async () => ({
              identity_mode: "authenticated",
              is_open: true,
            }),
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
          return {
            ok: true,
            status: 201,
            json: async () => ({ public_id: "v1" }),
          };
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

  it("requests an email voting token when the visible form button is clicked", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(async (input: unknown, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/status/"))
          return {
            ok: true,
            json: async () => ({ identity_mode: "email_link", is_open: true }),
          };
        if (url.endsWith("/results/"))
          return { ok: false, status: 403, json: async () => ({}) };
        if (url.endsWith("/request-email-token/") && init?.method === "POST") {
          return { ok: true, json: async () => ({ token: "token" }) };
        }
        return { ok: true, json: async () => [] };
      });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<CommunityVoting eventId="e1" />));
    await waitFor(
      () =>
        container.querySelector<HTMLInputElement>('input[type="email"]') !==
        null,
    );
    await act(async () => {
      const input = container.querySelector<HTMLInputElement>(
        'input[type="email"]',
      )!;
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set?.call(input, "voter@example.com");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((button) => button.textContent === "Request a voting link")
        ?.click(),
    );
    await waitFor(
      () => container.textContent?.includes("using it here directly") ?? false,
    );
    expect(
      fetchMock.mock.calls.some(
        ([url, init]) =>
          String(url).endsWith("request-email-token/") &&
          init?.method === "POST",
      ),
    ).toBe(true);
  });

  it("shows a retry control when voting status fails to load", async () => {
    let attempts = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: unknown) => {
        if (String(input).endsWith("/status/")) {
          attempts += 1;
          return attempts === 1
            ? { ok: false, status: 503, json: async () => ({}) }
            : {
                ok: true,
                status: 200,
                json: async () => ({
                  identity_mode: "authenticated",
                  is_open: false,
                }),
              };
        }
        return { ok: false, status: 403, json: async () => ({}) };
      }),
    );
    act(() => root.render(<CommunityVoting eventId="e1" />));
    await waitFor(
      () =>
        container.textContent?.includes("Could not load voting (503)") ?? false,
    );
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((button) => button.textContent === "Try again")
        ?.click(),
    );
    await waitFor(
      () =>
        container.textContent?.includes("Voting is not currently open") ??
        false,
    );
    expect(attempts).toBe(2);
  });
});
