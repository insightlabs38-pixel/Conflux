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

  it("runs a dry run against the chosen endpoint and subject", async () => {
    let requestBody: unknown = null;
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation(async (path: string, options?: RequestInit) => {
          if (path.endsWith("authz-dry-run/") && options?.method === "POST") {
            requestBody = JSON.parse(String(options.body));
            return {
              ok: true,
              json: async () => ({ allowed: false, mode: "hypothetical" }),
            };
          }
          return { ok: true, json: async () => MATRIX };
        }),
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

    const selects = [...container.querySelectorAll("select")];
    const endpointSelect = selects.find((select) =>
      [...select.options].some((option) => option.value.includes("|")),
    )!;
    await act(async () => {
      endpointSelect.value = "POST|api/v1/.../tracks/";
      endpointSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await act(async () => {
      const testButton = [...container.querySelectorAll("button")].find(
        (button) => button.textContent === "Test",
      );
      testButton?.click();
    });
    await waitFor(() => container.textContent?.includes("Denied") ?? false);
    expect(requestBody).toEqual({
      path: "api/v1/.../tracks/",
      method: "POST",
      subject_kind: "role",
      subject: "participant",
    });

    await act(async () => root.unmount());
    container.remove();
  });
});
