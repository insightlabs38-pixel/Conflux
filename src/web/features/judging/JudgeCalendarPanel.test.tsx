// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { JudgeCalendarPanel } from "./JudgeCalendarPanel";

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
  throw new Error("Judge calendar panel did not update");
}

it("shows event windows and per-plan progress", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        windows: [
          {
            name: "Judging window",
            opens_at: null,
            closes_at: null,
            status: "open",
          },
        ],
        assignments: [
          {
            stage_name: "Finals",
            plan: "p1",
            plan_name: "Panel",
            rubric_published: true,
            assigned_count: 3,
            submitted_count: 1,
            completion_ratio: 0.33,
          },
        ],
      }),
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<JudgeCalendarPanel workspaceId="w1" eventId="e1" />));

  await until(() => container.textContent?.includes("Judging window") ?? false);
  expect(container.textContent).toContain("1/3 submitted");

  act(() => root.unmount());
  container.remove();
});

it("shows an empty state when the judge has no assignments yet", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ windows: [], assignments: [] }),
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<JudgeCalendarPanel workspaceId="w1" eventId="e1" />));

  await until(
    () => container.textContent?.includes("no assigned candidates") ?? false,
  );

  act(() => root.unmount());
  container.remove();
});
