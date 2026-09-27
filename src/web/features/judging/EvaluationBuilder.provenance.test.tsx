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
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Provenance explorer did not update");
}

it("shows the frozen score chain and switches to another project", async () => {
  const fetchMock = vi.fn(async (input: unknown) => {
    const url = String(input);
    let body: unknown;
    if (url.endsWith("stages/")) body = [{ public_id: "s1", name: "Final" }];
    else if (url.endsWith("evaluation-pools/")) body = [];
    else if (url.endsWith("evaluation-plans/"))
      body = [
        {
          public_id: "plan-1",
          name: "Panel",
          draft_criteria: [],
          pool_strategy: "all_judges",
          prize_judging: false,
          results_visible_to_participants: false,
          feedback_visible_to_participants: false,
          feedback_anonymous: false,
          current_rubric_version: 1,
        },
      ];
    else if (url.endsWith("progress/"))
      body = {
        submitted_ballots: 2,
        expected_ballots: 2,
        completion_ratio: 1,
        results_published: true,
      };
    else if (url.endsWith("results/"))
      body = [
        { project: "p1", project_name: "Alpha", rank: 1 },
        { project: "p2", project_name: "Beta", rank: 2 },
      ];
    else if (url.endsWith("provenance/p1/"))
      body = {
        project_name: "Alpha",
        rank: 1,
        raw_score: 6.5,
        final_score: 7,
        tie_break: null,
        normalization_run: "run-1",
        ridge_lambda: 1,
        converged: true,
        grand_mean: 6,
        ballot_snapshot_available: true,
        ballots: [
          {
            ballot: "b1",
            judge: "j1",
            rubric_version: "r1",
            responses: [
              {
                criterion_id: "impact",
                criterion_name: "Impact",
                weight: 2,
                score: 6,
              },
            ],
            weighted_score: 6,
            judge_effect: -1,
            adjusted_score: 7,
          },
        ],
        awards: [
          {
            award: "a1",
            name: "Grand Prize",
            rank_at_selection: 1,
            override_reason: "",
            published: true,
          },
        ],
      };
    else if (url.endsWith("provenance/p2/"))
      body = {
        project_name: "Beta",
        rank: 2,
        raw_score: 5,
        final_score: 5,
        tie_break: null,
        normalization_run: "run-1",
        ridge_lambda: 1,
        converged: true,
        grand_mean: 6,
        ballot_snapshot_available: false,
        ballots: null,
        awards: [],
      };
    else throw new Error(`Unexpected request: ${url}`);
    return { ok: true, status: 200, json: async () => body };
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  try {
    act(() => root.render(<EvaluationBuilder workspaceId="w" eventId="e" />));
    await until(() => container.textContent?.includes("Final") ?? false);
    const stage = container.querySelector("select") as HTMLSelectElement;
    await act(async () => {
      stage.value = "s1";
      stage.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await until(() => container.textContent?.includes("Grand Prize") ?? false);
    expect(container.textContent).toContain("Impact: 6 (weight 2)");
    expect(container.textContent).toContain("normalized 7.00");

    const project = container.querySelector(
      'select[aria-label="Project provenance"]',
    ) as HTMLSelectElement;
    await act(async () => {
      project.value = "p2";
      project.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await until(
      () => container.textContent?.includes("snapshot unavailable") ?? false,
    );
    expect(container.textContent).toContain("Beta");
    expect(container.textContent).not.toContain("Grand Prize");
  } finally {
    act(() => root.unmount());
    container.remove();
  }
});
