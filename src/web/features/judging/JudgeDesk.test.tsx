// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { JudgeWorkspace } from "./JudgeWorkspace";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;

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

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 400; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error(`Judge desk did not update: ${container.textContent}`);
}

async function choose(select: HTMLSelectElement, value: string) {
  await act(async () => {
    select.value = value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
}

function button(name: string) {
  return [...container.querySelectorAll("button")].find(
    (item) => item.textContent?.trim() === name,
  ) as HTMLButtonElement | undefined;
}

function stubDesk() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: unknown) => {
      const url = String(input);
      const body = url.endsWith("judge-events/")
        ? [{ public_id: "e1", name: "First" }]
        : url.endsWith("judge-calendar/")
          ? { windows: [], assignments: [] }
          : url.endsWith("/e1/stages/")
            ? [{ public_id: "s1", name: "Final" }]
            : url.endsWith("/s1/evaluation-plans/")
              ? [{ public_id: "p1", name: "Review" }]
              : url.endsWith("candidates/")
                ? [
                    { project: "a", name: "Alpha", status: "submitted" },
                    { project: "b", name: "Bravo", status: "pending" },
                    { project: "c", name: "Charlie", status: "drafted" },
                  ]
                : url.endsWith("publish-rubric/")
                  ? {
                      number: 1,
                      criteria: [
                        {
                          id: "k",
                          name: "Impact",
                          weight: 3,
                          min_score: 1,
                          max_score: 10,
                          anchors: { "10": "Outstanding" },
                        },
                      ],
                    }
                  : url.endsWith("my-assignments/")
                    ? [
                        {
                          project: "a",
                          name: "Alpha",
                          status: "accepted",
                          reason: "",
                        },
                        {
                          project: "b",
                          name: "Bravo",
                          status: "declined",
                          reason: "COI",
                        },
                        {
                          project: "c",
                          name: "Charlie",
                          status: "pending",
                          reason: "",
                        },
                      ]
                    : url.includes("my-route/")
                      ? {
                          stops: [
                            {
                              project: "b",
                              project_name: "Bravo",
                              location_name: "Table 4",
                              room: "Hall A",
                            },
                          ],
                          total_distance: 0,
                          baseline_distance: 0,
                          unplaced: [],
                          already_evaluated: 1,
                        }
                      : [];
      return { ok: true, status: 200, json: async () => body };
    }),
  );
}

async function openPlan() {
  act(() => root.render(<JudgeWorkspace workspaceId="w" />));
  await waitFor(() => container.textContent?.includes("First") ?? false);
  await choose(container.querySelector("select")!, "e1");
  await waitFor(() => container.querySelectorAll("select").length > 1);
  await choose(container.querySelectorAll("select")[1], "s1");
  await waitFor(() => container.textContent?.includes("Alpha") ?? false);
}

describe("judge desk", () => {
  it("summarizes progress, the next project, recusal and route", async () => {
    stubDesk();
    await openPlan();
    await waitFor(
      () =>
        container.querySelector('[aria-label="Your judging summary"]') !==
          null &&
        (container.textContent?.includes("Hall A / Table 4") ?? false),
    );
    const summary = container.querySelector(
      '[aria-label="Your judging summary"]',
    )!;
    expect(summary.textContent).toContain("1 of 3");
    expect(summary.textContent).toContain("2 remaining");
    expect(summary.textContent).toContain("Bravo");
    expect(summary.textContent).toContain("Recused");
    expect(container.textContent).toContain("Next stop");
  });

  it("offers project position, weights, recusal and previous/next", async () => {
    stubDesk();
    await openPlan();
    await act(async () => button("Bravo")!.click());
    await waitFor(
      () => container.textContent?.includes("Project 2 of 3") ?? false,
    );
    expect(container.textContent).toContain("Weight 3");
    expect(container.textContent).toContain("0 of 1 criteria scored");
    expect(button("Recuse or report a conflict")).toBeTruthy();
    expect(button("Submit and continue")).toBeTruthy();
    await act(async () => button("Next project")!.click());
    await waitFor(
      () => container.textContent?.includes("Project 3 of 3") ?? false,
    );
    expect(button("Next project")!.disabled).toBe(true);
    await act(async () => button("Previous project")!.click());
    await waitFor(
      () => container.textContent?.includes("Project 2 of 3") ?? false,
    );
  });
});
