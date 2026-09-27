// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { EvaluationBuilder } from "./EvaluationBuilder";

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
  throw new Error("Evaluation builder did not update");
}

const plan = {
  public_id: "plan-1",
  name: "Panel",
  candidate_type: "project",
  pool_strategy: "all_judges",
  pool: null,
  prize_judging: false,
  results_visible_to_participants: false,
  feedback_visible_to_participants: false,
  feedback_anonymous: true,
  draft_criteria: [],
  current_rubric_version: null,
  published_normalization_run: null,
};

it("releasing feedback PATCHes the plan and the toggle reflects the response", async () => {
  const fetchMock = vi
    .fn()
    .mockImplementation(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("stages/"))
        return {
          ok: true,
          json: async () => [{ public_id: "s1", name: "Final" }],
        };
      if (url.endsWith("evaluation-pools/"))
        return { ok: true, json: async () => [] };
      if (url.endsWith("evaluation-plans/"))
        return { ok: true, json: async () => [plan] };
      if (url.endsWith("plan-1/") && init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        expect(body).toEqual({ feedback_visible_to_participants: true });
        return { ok: true, json: async () => ({ ...plan, ...body }) };
      }
      throw new Error(`Unexpected request: ${url}`);
    });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<EvaluationBuilder workspaceId="w1" eventId="e1" />));
  await until(() => container.textContent?.includes("Final") ?? false);

  const stageSelect = container.querySelector("select") as HTMLSelectElement;
  await act(async () => {
    stageSelect.value = "s1";
    stageSelect.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await until(
    () =>
      container.textContent?.includes(
        "Judge feedback visible to participants",
      ) ?? false,
  );

  const feedbackToggle = Array.from(
    container.querySelectorAll('input[type="checkbox"]'),
  ).find((input) =>
    input
      .closest("label")
      ?.textContent?.includes("Judge feedback visible to participants"),
  ) as HTMLInputElement;
  expect(feedbackToggle.checked).toBe(false);
  await act(async () => feedbackToggle.click());

  await until(() => feedbackToggle.checked);
  expect(
    fetchMock.mock.calls.some(([, init]) => init?.method === "PATCH"),
  ).toBe(true);

  act(() => root.unmount());
  container.remove();
});
