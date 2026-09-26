// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspaceSelector } from "./WorkspaceSelector";

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

function mockMe(status: number, body?: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
    }),
  );
}

describe("WorkspaceSelector", () => {
  it("lists the current user's authorized workspaces, deduped by workspace, and reports selection", async () => {
    mockMe(200, {
      public_id: "u1",
      username: "organizer",
      memberships: [
        {
          workspace: "w1",
          workspace_name: "Regionals",
          workspace_slug: "regionals",
          role: "organizer",
        },
        {
          workspace: "w1",
          workspace_name: "Regionals",
          workspace_slug: "regionals",
          role: "judge",
        },
        {
          workspace: "w2",
          workspace_name: "Finals",
          workspace_slug: "finals",
          role: "organizer",
        },
      ],
    });
    const onSelect = vi.fn();
    act(() => {
      root.render(<WorkspaceSelector onSelect={onSelect} />);
    });
    await waitFor(() => container.querySelectorAll("button").length > 0);

    const buttons = container.querySelectorAll("button");
    expect(buttons).toHaveLength(2);
    expect(container.textContent).toContain("Regionals");
    expect(container.textContent).toContain("Finals");

    (buttons[0] as HTMLButtonElement).click();
    expect(onSelect).toHaveBeenCalledWith("w1");
  });

  it("shows an empty state when the user has no workspaces", async () => {
    mockMe(200, { public_id: "u1", username: "organizer", memberships: [] });
    act(() => {
      root.render(<WorkspaceSelector onSelect={vi.fn()} />);
    });
    await waitFor(() => container.textContent !== "Loading your workspaces…");
    expect(container.textContent).toContain("not a member of any workspace");
    expect(container.querySelectorAll("button")).toHaveLength(0);
  });

  it("prompts sign-in instead of listing workspaces when unauthenticated", async () => {
    mockMe(401);
    act(() => {
      root.render(<WorkspaceSelector onSelect={vi.fn()} />);
    });
    await waitFor(() => container.textContent !== "Loading your workspaces…");
    expect(container.textContent).toContain("Sign in");
    expect(container.querySelectorAll("button")).toHaveLength(0);
  });
});
