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
  throw new Error("Judge workspace did not update");
}

async function choose(select: HTMLSelectElement, value: string) {
  await act(async () => {
    select.value = value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
}

describe("judge navigation", () => {
  it("shows an empty state when no events are available", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));
    act(() => root.render(<JudgeWorkspace workspaceId="w" />));
    await waitFor(() => container.textContent?.includes("No events are available for judging") ?? false);
    expect(container.textContent).not.toContain("Loading judging events");
  });

  it("clears the old review queue when switching events", async () => {
    const fetchMock = vi.fn().mockImplementation(async (input: unknown) => {
      const url = String(input);
      const body = url.endsWith("judge-events/")
        ? [
            { public_id: "e1", name: "First" },
            { public_id: "e2", name: "Second" },
          ]
        : url.includes("/e1/stages/") && url.endsWith("/stages/")
          ? [{ public_id: "s1", name: "Final" }]
          : url.includes("/s1/evaluation-plans/") &&
              url.endsWith("evaluation-plans/")
            ? [{ public_id: "p1", name: "Final review" }]
            : url.endsWith("candidates/")
              ? [{ project: "project", name: "Old project", status: "pending" }]
              : url.endsWith("publish-rubric/")
                ? { number: 1, criteria: [] }
                : [];
      return { ok: true, status: 200, json: async () => body };
    });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<JudgeWorkspace workspaceId="w" />));
    await waitFor(() => container.textContent?.includes("Second") ?? false);
    await choose(container.querySelector("select")!, "e1");
    await waitFor(() => container.textContent?.includes("Final") ?? false);
    await choose(container.querySelectorAll("select")[1], "s1");
    await waitFor(
      () => container.textContent?.includes("Old project") ?? false,
    );
    await choose(container.querySelector("select")!, "e2");
    expect(container.textContent).not.toContain("Old project");
    expect(container.querySelectorAll("select")).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("judge-events/"),
      expect.anything(),
    );
  });

  it("keeps a rejected draft visibly unsaved and prevents ballot submission", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(async (input: unknown, options?: RequestInit) => {
        const url = String(input);
        const body = url.endsWith("judge-events/")
          ? [{ public_id: "e1", name: "First" }]
          : url.endsWith("/stages/")
            ? [{ public_id: "s1", name: "Final" }]
            : url.endsWith("evaluation-plans/")
              ? [{ public_id: "p1", name: "Review" }]
              : url.endsWith("candidates/")
                ? [{ project: "project", name: "Project", status: "pending" }]
                : url.endsWith("publish-rubric/")
                  ? {
                      number: 1,
                      criteria: [
                        {
                          id: "impact",
                          name: "Impact",
                          min_score: 0,
                          max_score: 10,
                          anchors: {},
                        },
                      ],
                    }
                  : url.endsWith("/draft/")
                    ? null
                    : [];
        if (url.endsWith("/draft/") && options?.method === "PUT") {
          return {
            ok: false,
            status: 503,
            json: async () => ({ detail: "Unavailable" }),
          };
        }
        return { ok: true, status: 200, json: async () => body };
      });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<JudgeWorkspace workspaceId="w" />));
    await waitFor(() => container.textContent?.includes("First") ?? false);
    await choose(container.querySelector("select")!, "e1");
    await waitFor(() => container.textContent?.includes("Final") ?? false);
    await choose(container.querySelectorAll("select")[1], "s1");
    await waitFor(() => container.textContent?.includes("Project") ?? false);
    const projectButton = [...container.querySelectorAll("button")].find(
      (button) => button.textContent === "Project",
    );
    act(() => projectButton?.click());
    await waitFor(
      () =>
        container.querySelector<HTMLInputElement>('input[type="number"]')
          ?.disabled === false,
    );
    const score = container.querySelector<HTMLInputElement>(
      'input[type="number"]',
    )!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set?.call(score, "7");
      score.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await waitFor(
      () => container.textContent?.includes("Draft not saved") ?? false,
    );
    expect(container.textContent).toContain("Unsaved changes");
    expect(container.textContent).toContain("Retry draft save");
    const submit = [...container.querySelectorAll("button")].find(
      (button) => button.textContent === "Submit ballot",
    );
    await act(async () => submit?.click());
    await waitFor(
      () => container.textContent?.includes("Unavailable") ?? false,
    );
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url).endsWith("/ballots/") && options?.method === "POST",
      ),
    ).toBe(false);
  });
});
