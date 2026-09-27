// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { MarketplacePanel } from "./MarketplacePanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function until(check: () => boolean) {
  for (let index = 0; index < 100; index++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Marketplace did not update");
}

describe("team marketplace", () => {
  it("lets an unteamed participant opt into discovery and see project openings", async () => {
    let profile: object | null = null;
    const opening = {
      public_id: "o1",
      team_name: "Builders",
      project_name: "Robot",
      title: "Designer",
      description: "Help with UI",
      desired_skills: ["design"],
      matched_skills: [],
      is_open: true,
    };
    const fetcher = vi
      .fn()
      .mockImplementation(async (path: string, options?: RequestInit) => {
        let body: unknown = [];
        if (path.endsWith("my-team/")) body = { team: null, my_role: null };
        else if (path.endsWith("marketplace/profile/")) {
          if (options?.method === "PUT") {
            profile = {
              public_id: "p1",
              username: "alice",
              ...JSON.parse(String(options.body)),
            };
            body = profile;
          } else body = { profile };
        } else if (
          path.endsWith("marketplace/matches/") ||
          path.endsWith("marketplace/openings/")
        )
          body = [opening];
        return { ok: true, json: async () => body };
      });
    vi.stubGlobal("fetch", fetcher);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(<MarketplacePanel workspaceId="w" eventId="e" />),
    );
    await until(() => container.textContent?.includes("Robot") ?? false);
    expect(container.textContent).toContain("Designer");
    const skills = container.querySelector("form input") as HTMLInputElement;
    const visible = container.querySelector(
      'input[type="checkbox"]',
    ) as HTMLInputElement;
    await act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set?.call(skills, "Design");
      skills.dispatchEvent(new Event("input", { bubbles: true }));
      visible.click();
    });
    await act(async () => {
      [...container.querySelectorAll("button")]
        .find((button) => button.textContent === "Save profile")
        ?.click();
    });
    await until(
      () =>
        container.textContent?.includes("Your profile is visible.") ?? false,
    );
    expect(
      fetcher.mock.calls.some(
        ([path, options]) =>
          String(path).endsWith("marketplace/profile/") &&
          options?.method === "PUT" &&
          JSON.parse(String(options.body)).visible === true,
      ),
    ).toBe(true);
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});
