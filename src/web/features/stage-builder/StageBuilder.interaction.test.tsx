// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { StageBuilder } from "./StageBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Stage builder did not update");
}

const presets = {
  two_round: {
    label: "Two rounds: Screening → Final",
    rounds: ["Screening", "Final"],
  },
};

it("applies a workflow preset and then hides the preset picker", async () => {
  let applied = false;
  const fetchMock = vi
    .fn()
    .mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("workflow-presets/apply/")) {
        expect(init?.method).toBe("POST");
        expect(JSON.parse(String(init?.body))).toEqual({ preset: "two_round" });
        applied = true;
        return { ok: true, json: async () => ({ stages: [], plans: [] }) };
      }
      if (url.endsWith("workflow-presets/"))
        return { ok: true, json: async () => presets };
      if (url.endsWith("/stages/"))
        return {
          ok: true,
          json: async () =>
            applied
              ? [
                  {
                    public_id: "s1",
                    name: "Screening",
                    position: 0,
                    is_initial: true,
                    participation_mode: "team_formation",
                  },
                ]
              : [],
        };
      if (url.endsWith("stage-transitions/"))
        return { ok: true, json: async () => [] };
      if (url.endsWith("stage-graph/validate/"))
        return { ok: true, json: async () => ({ valid: true, order: [] }) };
      if (url.endsWith("stage-evidence/"))
        return { ok: true, json: async () => [] };
      if (url.endsWith("advance/"))
        return { ok: true, json: async () => ({ strategies: [] }) };
      throw new Error(`Unexpected request: ${url}`);
    });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<StageBuilder workspaceId="w1" eventId="e1" />));
  await until(
    () => container.textContent?.includes("Apply a workflow preset") ?? false,
  );

  const select = container.querySelector("select") as HTMLSelectElement;
  await act(async () => {
    select.value = "two_round";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  const applyButton = Array.from(container.querySelectorAll("button")).find(
    (button) => button.textContent === "Apply preset",
  )!;
  await act(async () => applyButton.click());

  await until(() => container.textContent?.includes("Screening") ?? false);
  expect(applied).toBe(true);
  expect(container.textContent).not.toContain("Apply a workflow preset");

  act(() => root.unmount());
  container.remove();
});
