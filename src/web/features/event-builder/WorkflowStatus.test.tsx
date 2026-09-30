// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import { WorkflowStatus } from "./WorkflowStatus";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const preset = { key: "hackathon", version: 1, label: "Hackathon" };

async function mount(respond: (url: string) => Response) {
  const fetchMock = vi.fn(async (input: unknown) => respond(String(input)));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(withQuery(<WorkflowStatus workspaceId="w" eventId="e1" />)),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, fetchMock, root };
}

describe("WorkflowStatus", () => {
  it("says the event follows its format and that editing only customizes what changed", async () => {
    const { container, fetchMock, root } = await mount(() =>
      jsonResponse(200, {
        source: "preset",
        preset,
        stages: ["Build", "Judging", "Final"],
        differences: [],
      }),
    );
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/events/e1/workflow/",
    );
    expect(container.textContent).toContain("Follows the format");
    expect(container.textContent).toContain("only that part becomes custom");
    await act(async () => root.unmount());
  });

  it("names each difference once the workflow was customized, and can be rechecked", async () => {
    let calls = 0;
    const { container, root } = await mount(() => {
      calls += 1;
      return jsonResponse(200, {
        source: "custom",
        preset,
        stages: ["Build", "Demo"],
        differences: [
          { code: "stage_added", message: "Stage 'Demo' was added." },
          {
            code: "plan_removed",
            message: "Judging was removed from 'Final'.",
          },
        ],
      });
    });
    expect(container.textContent).toContain("Customized");
    expect(container.textContent).toContain("Stage 'Demo' was added.");
    expect(container.textContent).toContain(
      "Judging was removed from 'Final'.",
    );
    const button = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Check again",
    )!;
    await act(async () => button.click());
    expect(calls).toBe(2);
    await act(async () => root.unmount());
  });

  it("explains an event built by hand and surfaces a failed load with a retry", async () => {
    const hand = await mount(() =>
      jsonResponse(200, {
        source: "none",
        preset: null,
        stages: ["Only"],
        differences: [],
      }),
    );
    expect(hand.container.textContent).toContain("Built by hand");
    expect(hand.container.textContent).toContain("entirely yours");
    await act(async () => hand.root.unmount());

    const failed = await mount(() =>
      jsonResponse(500, { detail: "Server exploded" }),
    );
    expect(failed.container.querySelector("[role=alert]")).not.toBeNull();
    expect(failed.container.textContent).toContain("Try again");
    await act(async () => failed.root.unmount());
  });
});
