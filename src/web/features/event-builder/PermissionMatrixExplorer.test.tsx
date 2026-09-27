// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PermissionMatrixExplorer } from "./PermissionMatrixExplorer";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Explorer did not update");
}

const MATRIX = [
  {
    resource: "events",
    view: "TrackListView",
    path: "api/v1/.../tracks/",
    method: "POST",
    access: "roles",
    roles: ["organizer", "admin"],
  },
  {
    resource: "evaluations",
    view: "BallotListCreateView",
    path: "api/v1/.../ballots/",
    method: "POST",
    access: "roles",
    roles: ["judge", "organizer", "admin"],
  },
  {
    resource: "events",
    view: "MyEventApplicationView",
    path: "api/v1/.../my-application/",
    method: "POST",
    access: "any_authenticated",
    roles: [],
  },
  {
    resource: "events",
    view: "PublicEventView",
    path: "api/v1/events/.../",
    method: "GET",
    access: "public",
    roles: [],
  },
];

describe("permission matrix explorer", () => {
  it("filters endpoints by role, always including any-authenticated and public ones", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => MATRIX }),
    );
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(<PermissionMatrixExplorer workspaceId="w" eventId="e" />),
    );
    await waitFor(
      () => container.textContent?.includes("TrackListView") ?? false,
    );
    expect(container.textContent).toContain("BallotListCreateView");
    expect(container.textContent).toContain("MyEventApplicationView");
    expect(container.textContent).toContain("PublicEventView");

    const select = container.querySelector("select") as HTMLSelectElement;
    await act(async () => {
      select.value = "judge";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(container.textContent).not.toContain("TrackListView");
    expect(container.textContent).toContain("BallotListCreateView");
    expect(container.textContent).toContain("MyEventApplicationView");
    expect(container.textContent).toContain("PublicEventView");

    await act(async () => root.unmount());
    container.remove();
  });
});
