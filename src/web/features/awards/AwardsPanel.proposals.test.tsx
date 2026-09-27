// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { AwardsPanel } from "./AwardsPanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function until(check: () => boolean) {
  for (let index = 0; index < 100; index++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Award preview did not update");
}

describe("award allocation preview", () => {
  it("shows a suggestion and prepares it for explicit winner selection", async () => {
    const fetcher = vi.fn().mockImplementation(async (path: string) => {
      let body: unknown = [];
      if (path.endsWith("/awards/"))
        body = [
          {
            public_id: "award-1",
            name: "Prize",
            selection_source: "manual",
            winner_count: 1,
            eligibility_track: null,
            require_finalized_submission: false,
            published_at: null,
            winners: [],
            components: [],
          },
        ];
      else if (path.endsWith("/awards/candidates/"))
        body = [
          {
            public_id: "project-1",
            name: "Project",
            track: null,
            has_finalized_submission: false,
          },
        ];
      else if (path.endsWith("/awards/proposals/"))
        body = {
          search_limited: false,
          awards: [
            {
              award: "award-1",
              name: "Prize",
              existing: [],
              proposed: ["project-1"],
              unfilled: 0,
              blocker: null,
            },
          ],
        };
      return { ok: true, status: 200, json: async () => body };
    });
    vi.stubGlobal("fetch", fetcher);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    try {
      await act(async () =>
        root.render(<AwardsPanel workspaceId="w" eventId="e" />),
      );
      await until(
        () => container.textContent?.includes("Preview allocations") ?? false,
      );
      await act(async () => {
        [...container.querySelectorAll("button")]
          .find((button) => button.textContent === "Preview allocations")
          ?.click();
      });
      await until(
        () => container.textContent?.includes("Use Project") ?? false,
      );
      await act(async () => {
        [...container.querySelectorAll("button")]
          .find((button) => button.textContent === "Use Project")
          ?.click();
      });
      const selectedAward = [...container.querySelectorAll("select")].find(
        (select) =>
          select.closest("label")?.textContent?.includes("Manage award"),
      );
      const selectedProject = [...container.querySelectorAll("select")].find(
        (select) =>
          select.closest("label")?.textContent?.includes("Winning project"),
      );
      expect(selectedAward?.value).toBe("award-1");
      expect(selectedProject?.value).toBe("project-1");
      expect(
        fetcher.mock.calls.every(
          ([, options]) => !options || options.method === "GET",
        ),
      ).toBe(true);
    } finally {
      await act(async () => root.unmount());
      container.remove();
      vi.unstubAllGlobals();
    }
  });
});
