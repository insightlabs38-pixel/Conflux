// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { JudgeExpertisePanel } from "./JudgeExpertisePanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 50; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Expertise UI did not update");
}

it("saves structured tags from the judge workspace", async () => {
  const fetchMock = vi.fn(async (_url: unknown, init?: RequestInit) => ({
    ok: true,
    json: async () => {
      if (init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual({
          tags: ["AI", "Data Science"],
        });
        return { judge: "j1", tags: ["ai", "data science"], updated_at: "now" };
      }
      return { judge: "j1", tags: [], updated_at: null };
    },
  }));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<JudgeExpertisePanel workspaceId="w1" />));
  await until(() => container.querySelector("input") !== null);
  const input = container.querySelector("input") as HTMLInputElement;
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )?.set?.call(input, "AI, Data Science");
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await act(async () =>
    (container.querySelector("button") as HTMLButtonElement).click(),
  );
  await until(
    () => container.textContent?.includes("Saved: ai, data science") ?? false,
  );
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/workspaces/w1/my-judge-expertise/",
    expect.objectContaining({ method: "PUT" }),
  );
  await act(async () => root.unmount());
});
