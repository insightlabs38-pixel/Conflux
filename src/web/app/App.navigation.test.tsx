// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

// Silences a benign act() warning; happy-dom doesn't set this itself.
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

// Polls rather than a fixed number of ticks: React's scheduler doesn't
// reliably flush within plain setTimeout(0) hops under happy-dom.
async function waitFor(check: () => boolean, timeoutMs = 1000) {
  const start = Date.now();
  while (!check()) {
    if (Date.now() - start > timeoutMs) throw new Error("waitFor timed out");
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
}

// Routes the two endpoints App's tree actually calls: accounts/me and the events list.
function mockApi(
  meStatus: number,
  meBody: unknown,
  eventsStatus: number,
  eventsBody: unknown,
) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: unknown) => {
      const url = String(input);
      if (url.includes("/accounts/me/")) {
        return {
          ok: meStatus >= 200 && meStatus < 300,
          status: meStatus,
          json: async () => meBody,
        };
      }
      return {
        ok: eventsStatus >= 200 && eventsStatus < 300,
        status: eventsStatus,
        json: async () => eventsBody,
      };
    }),
  );
}

describe("App navigation", () => {
  it("opens the participant team picker from workspace selection", async () => {
    window.history.pushState({}, "", "/");
    mockApi(
      200,
      {
        public_id: "u1",
        username: "member",
        memberships: [
          {
            workspace: "w1",
            workspace_name: "Regionals",
            workspace_slug: "regionals",
            role: "participant",
          },
        ],
      },
      200,
      [],
    );
    act(() => {
      root.render(<App />);
    });
    await waitFor(() => container.querySelector("button") !== null);
    act(() => {
      container.querySelector("button")?.click();
    });
    await waitFor(
      () =>
        container.querySelector('[aria-label="Participant events"]') !== null,
    );
    await waitFor(
      () =>
        container.textContent?.includes(
          "No events are open for participation.",
        ) ?? false,
    );
    expect(container.textContent).toContain(
      "No events are open for participation.",
    );
  });

  it("reaches the event dashboard for an authorized workspace through normal selection", async () => {
    window.history.pushState({}, "", "/");
    mockApi(
      200,
      {
        public_id: "u1",
        username: "organizer",
        memberships: [
          {
            workspace: "w1",
            workspace_name: "Regionals",
            workspace_slug: "regionals",
            role: "organizer",
          },
        ],
      },
      200,
      [],
    );
    act(() => {
      root.render(<App />);
    });
    await waitFor(() => container.querySelectorAll("button").length > 0);

    const selectButton = container.querySelector("button");
    expect(selectButton?.textContent).toContain("Regionals");
    act(() => {
      (selectButton as HTMLButtonElement).click();
    });
    await waitFor(
      () => container.querySelector('[aria-label="Event dashboard"]') !== null,
    );

    expect(window.location.search).toContain("workspace=w1");
    expect(container.textContent).toContain("Back to workspaces");
  });

  it("routes a judge to their review workspace, not the organizer dashboard", async () => {
    window.history.pushState({}, "", "/");
    mockApi(
      200,
      {
        public_id: "u1",
        username: "judge",
        memberships: [
          {
            workspace: "w1",
            workspace_name: "Regionals",
            workspace_slug: "regionals",
            role: "judge",
          },
        ],
      },
      200,
      [],
    );
    act(() => {
      root.render(<App />);
    });
    await waitFor(() => container.querySelectorAll("button").length > 0);
    act(() => {
      (container.querySelector("button") as HTMLButtonElement).click();
    });
    await waitFor(
      () => container.querySelector('[aria-label="Judging"]') !== null,
    );
    expect(
      container.querySelector('[aria-label="Event dashboard"]'),
    ).toBeNull();
  });

  it("denies a direct link to a workspace without membership and offers a way back", async () => {
    window.history.pushState({}, "", "/?workspace=not-a-real-workspace");
    mockApi(
      200,
      { public_id: "u1", username: "organizer", memberships: [] },
      403,
      {
        detail: "You do not have a role that permits this action.",
      },
    );
    act(() => {
      root.render(<App />);
    });

    await waitFor(
      () => container.textContent?.includes("Access denied") ?? false,
    );
    expect(
      container.querySelector('[aria-label="Event dashboard"]'),
    ).toBeNull();
    const backButton = [...container.querySelectorAll("button")].find(
      (button) => button.textContent === "Back to workspaces",
    );
    expect(backButton).toBeDefined();

    act(() => {
      backButton?.click();
    });

    expect(window.location.search).toBe("");
    expect(
      container.querySelector('[aria-label="Event dashboard"]'),
    ).toBeNull();
  });

  it("waits for membership before showing a direct linked organizer dashboard", async () => {
    window.history.pushState({}, "", "/?workspace=w1");
    let resolveMe!: (value: unknown) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        if (String(input).includes("/accounts/me/")) {
          return new Promise((resolve) => {
            resolveMe = resolve;
          });
        }
        return Promise.resolve({ ok: true, status: 200, json: async () => [] });
      }),
    );
    act(() => root.render(<App />));
    expect(container.textContent).toContain("Checking workspace access");
    expect(
      container.querySelector('[aria-label="Event dashboard"]'),
    ).toBeNull();
    await act(async () =>
      resolveMe({
        ok: true,
        json: async () => ({
          memberships: [{ workspace: "w1", role: "organizer" }],
        }),
      }),
    );
    await waitFor(
      () => container.querySelector('[aria-label="Event dashboard"]') !== null,
    );
  });

  it("shows a retryable error when the membership check fails", async () => {
    window.history.pushState({}, "", "/?workspace=w1");
    mockApi(503, {}, 200, []);
    act(() => root.render(<App />));
    await waitFor(
      () =>
        container.textContent?.includes("Could not check workspace access") ??
        false,
    );
    expect(
      container.querySelector('[aria-label="Event dashboard"]'),
    ).toBeNull();
    expect(
      [...container.querySelectorAll("button")].some(
        (button) => button.textContent === "Try again",
      ),
    ).toBe(true);
  });

  it("clears participant event and invite context when returning to workspaces", async () => {
    window.history.pushState(
      {},
      "",
      "/?workspace=w1&event=missing&invite=secret",
    );
    mockApi(
      200,
      { memberships: [{ workspace: "w1", role: "participant" }] },
      200,
      [],
    );
    act(() => root.render(<App />));
    await waitFor(
      () =>
        container.textContent?.includes("not available for participation") ??
        false,
    );
    expect(
      container.querySelector('[aria-label="Participant events"]'),
    ).not.toBeNull();
    const back = [...container.querySelectorAll("button")].find(
      (button) => button.textContent === "Back to workspaces",
    );
    act(() => back?.click());
    expect(window.location.search).toBe("");
    expect(
      container.querySelector('[aria-label="Participant events"]'),
    ).toBeNull();
    await waitFor(
      () => container.querySelector('[aria-label="Your workspaces"]') !== null,
    );
  });

  it("routes a bare ?event= link to the public event site without requiring auth", async () => {
    window.history.pushState({}, "", "/?event=e1");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: unknown) => {
        const url = String(input);
        if (url.includes("/voting/")) {
          return { ok: false, status: 404, json: async () => ({}) };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({
            public_id: "e1",
            name: "Regionals",
            description: "",
            timezone: "UTC",
            starts_at: null,
            ends_at: null,
            status: "open",
            tracks: [],
            base_prizes: [],
          }),
        };
      }),
    );
    act(() => {
      root.render(<App />);
    });
    await waitFor(
      () =>
        container.querySelector('[aria-label="Regionals event page"]') !== null,
    );
    expect(container.textContent).not.toContain("Back to workspaces");
  });
});
