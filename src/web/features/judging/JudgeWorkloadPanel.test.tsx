// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { JudgeWorkloadPanel } from "./JudgeWorkloadPanel";

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
  throw new Error("Judge workload panel did not update");
}

it("renders a completion row per judge", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        {
          judge: "judge_b",
          assigned_count: 4,
          submitted_count: 0,
          completion_ratio: 0,
        },
        {
          judge: "judge_a",
          assigned_count: 4,
          submitted_count: 4,
          completion_ratio: 1,
        },
      ],
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<JudgeWorkloadPanel workspaceId="w1" eventId="e1" />));

  await until(() => container.textContent?.includes("judge_b") ?? false);
  expect(container.textContent).toContain("judge_a");
  expect(container.textContent).toContain("100%");

  act(() => root.unmount());
  container.remove();
});

it("shows an empty state when no judge has any assignment yet", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => [] }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<JudgeWorkloadPanel workspaceId="w1" eventId="e1" />));

  await until(
    () => container.textContent?.includes("No judge has any assigned") ?? false,
  );

  act(() => root.unmount());
  container.remove();
});
