// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { EvaluationBuilder } from "./EvaluationBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function until(check: () => boolean) {
  for (let index = 0; index < 100; index++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Judging builder did not update");
}

describe("prize judging setup", () => {
  it("creates a dedicated pool and sends its ID with the prize plan", async () => {
    const fetcher = vi
      .fn()
      .mockImplementation(async (path: string, options?: RequestInit) => {
        let body: unknown = [];
        if (path.endsWith("stages/"))
          body = [{ public_id: "s1", name: "Final" }];
        else if (
          path.endsWith("evaluation-pools/") &&
          options?.method === "POST"
        ) {
          body = { public_id: "pool-1", name: "Sponsor panel" };
        } else if (
          path.endsWith("evaluation-plans/") &&
          options?.method === "POST"
        ) {
          body = {
            public_id: "plan-1",
            name: "Prize",
            draft_criteria: [],
            pool_strategy: "all_judges",
            current_rubric_version: null,
            prize_judging: true,
          };
        }
        return { ok: true, status: 200, json: async () => body };
      });
    vi.stubGlobal("fetch", fetcher);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    try {
      await act(async () =>
        root.render(<EvaluationBuilder workspaceId="w" eventId="e" />),
      );
      await until(() => container.textContent?.includes("Final") ?? false);
      const stage = container.querySelector("select") as HTMLSelectElement;
      await act(async () => {
        stage.value = "s1";
        stage.dispatchEvent(new Event("change", { bubbles: true }));
      });
      await until(
        () => container.textContent?.includes("New pool name") ?? false,
      );
      const inputs = [...container.querySelectorAll("input")];
      const poolName = inputs.find((input) =>
        input.closest("label")?.textContent?.includes("New pool name"),
      ) as HTMLInputElement;
      await act(async () => {
        Object.getOwnPropertyDescriptor(
          HTMLInputElement.prototype,
          "value",
        )?.set?.call(poolName, "Sponsor panel");
        poolName.dispatchEvent(new Event("input", { bubbles: true }));
      });
      await act(async () => {
        [...container.querySelectorAll("button")]
          .find((button) => button.textContent === "Create pool")
          ?.click();
      });
      await until(
        () => container.textContent?.includes("Sponsor panel") ?? false,
      );
      const planName = [...container.querySelectorAll("input")].find((input) =>
        input.closest("label")?.textContent?.includes("New plan name"),
      ) as HTMLInputElement;
      await act(async () => {
        Object.getOwnPropertyDescriptor(
          HTMLInputElement.prototype,
          "value",
        )?.set?.call(planName, "Prize");
        planName.dispatchEvent(new Event("input", { bubbles: true }));
        (
          container.querySelector('input[type="checkbox"]') as HTMLInputElement
        ).click();
      });
      await act(async () => {
        [...container.querySelectorAll("button")]
          .find((button) => button.textContent === "Create evaluation plan")
          ?.click();
      });
      const post = fetcher.mock.calls.find(
        ([path, options]) =>
          String(path).endsWith("evaluation-plans/") &&
          options?.method === "POST",
      );
      expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({
        pool: "pool-1",
        prize_judging: true,
      });
    } finally {
      await act(async () => root.unmount());
      container.remove();
      vi.unstubAllGlobals();
    }
  });
});
