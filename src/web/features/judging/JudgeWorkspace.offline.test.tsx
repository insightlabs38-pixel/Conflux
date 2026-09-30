// @vitest-environment happy-dom
import { withRouter } from "../../lib/test-router";
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
  window.localStorage.clear();
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

const RUBRIC = {
  number: 1,
  criteria: [
    { id: "impact", name: "Impact", min_score: 0, max_score: 10, anchors: {} },
  ],
};

async function navigateToProject() {
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
}

async function scoreAndSubmit() {
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
  await act(async () => {
    const submit = [...container.querySelectorAll("button")].find(
      (button) => button.textContent === "Submit ballot",
    );
    submit?.click();
  });
}

describe("offline judge workspace", () => {
  it.each([false, true])(
    "syncs an offline ballot after browser restart=%s",
    async (restart) => {
      let online = true;
      let submitted = false;
      const fetchMock = vi
        .fn()
        .mockImplementation(async (input: unknown, options?: RequestInit) => {
          const url = String(input);
          if (url.endsWith("/accounts/me/"))
            return { ok: true, json: async () => ({ public_id: "judge-1" }) };
          if (url.endsWith("judge-events/"))
            return {
              ok: true,
              json: async () => [{ public_id: "e1", name: "First" }],
            };
          if (url.endsWith("judge-calendar/"))
            return {
              ok: true,
              json: async () => ({ windows: [], assignments: [] }),
            };
          if (url.endsWith("/stages/"))
            return {
              ok: true,
              json: async () => [{ public_id: "s1", name: "Final" }],
            };
          if (url.endsWith("evaluation-plans/"))
            return {
              ok: true,
              json: async () => [{ public_id: "p1", name: "Review" }],
            };
          if (url.endsWith("candidates/"))
            return {
              ok: true,
              json: async () => [
                {
                  project: "project",
                  name: "Project",
                  status: submitted ? "submitted" : "pending",
                },
              ],
            };
          if (url.endsWith("publish-rubric/"))
            return { ok: true, json: async () => RUBRIC };
          if (url.endsWith("/draft/")) {
            if (options?.method === "PUT" && !online)
              throw new TypeError("Failed to fetch");
            return { ok: true, json: async () => null };
          }
          if (url.endsWith("/ballots/") && options?.method === "POST") {
            if (!online) throw new TypeError("Failed to fetch");
            submitted = true;
            return { ok: true, status: 201, json: async () => ({}) };
          }
          return { ok: true, json: async () => [] };
        });
      vi.stubGlobal("fetch", fetchMock);
      act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
      await navigateToProject();

      online = false;
      await scoreAndSubmit();
      await waitFor(
        () => container.textContent?.includes("Queued offline") ?? false,
      );
      expect(container.textContent).toContain("1 ballot queued");

      if (restart) {
        await act(async () => root.unmount());
        root = createRoot(container);
        act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
        await waitFor(() => container.textContent?.includes("First") ?? false);
        await choose(container.querySelector("select")!, "e1");
        await waitFor(() => container.textContent?.includes("Final") ?? false);
        await choose(container.querySelectorAll("select")[1], "s1");
        await waitFor(
          () => container.textContent?.includes("1 ballot queued") ?? false,
        );
      }

      online = true;
      await act(async () => {
        window.dispatchEvent(new Event("online"));
      });
      await waitFor(
        () =>
          submitted &&
          !(container.textContent?.includes("1 ballot queued") ?? true),
      );
      expect(
        fetchMock.mock.calls.some(
          ([url, options]) =>
            String(url).endsWith("/ballots/") && options?.method === "POST",
        ),
      ).toBe(true);
    },
  );

  it("shows the last cached assignments and rubric when reopened offline", async () => {
    function navigationBody(url: string, online: boolean) {
      if (url.endsWith("/accounts/me/")) return { public_id: "judge-1" };
      if (url.endsWith("judge-events/"))
        return [{ public_id: "e1", name: "First" }];
      if (url.endsWith("judge-calendar/"))
        return { windows: [], assignments: [] };
      if (url.endsWith("/stages/")) return [{ public_id: "s1", name: "Final" }];
      if (url.endsWith("evaluation-plans/"))
        return [{ public_id: "p1", name: "Review" }];
      if (url.endsWith("candidates/")) {
        if (!online) throw new TypeError("Failed to fetch");
        return [{ project: "project", name: "Project", status: "pending" }];
      }
      if (url.endsWith("publish-rubric/")) {
        if (!online) throw new TypeError("Failed to fetch");
        return RUBRIC;
      }
      return [];
    }
    const onlineFetch = vi.fn().mockImplementation(async (input: unknown) => ({
      ok: true,
      status: 200,
      json: async () => navigationBody(String(input), true),
    }));
    vi.stubGlobal("fetch", onlineFetch);
    act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
    await navigateToProject();
    await act(async () => root.unmount());
    container.remove();

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    const offlineFetch = vi.fn().mockImplementation(async (input: unknown) => ({
      ok: true,
      status: 200,
      json: async () => navigationBody(String(input), false),
    }));
    vi.stubGlobal("fetch", offlineFetch);
    act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
    await waitFor(() => container.textContent?.includes("First") ?? false);
    await choose(container.querySelector("select")!, "e1");
    await waitFor(() => container.textContent?.includes("Final") ?? false);
    await choose(container.querySelectorAll("select")[1], "s1");
    await waitFor(
      () => container.textContent?.includes("You're offline") ?? false,
    );
    expect(container.textContent).toContain("Project");
  });

  describe("shared device", () => {
    const PLAN =
      "/api/v1/workspaces/w/events/e1/stages/s1/evaluation-plans/p1/";
    const queued = {
      project: "project",
      comment: "from judge one",
      responses: [{ criterion: "impact", score: 9 }],
    };

    function api(user: string) {
      return vi.fn().mockImplementation(async (input: unknown) => {
        const url = String(input);
        const body = url.endsWith("/accounts/me/")
          ? { public_id: user }
          : url.endsWith("judge-events/")
            ? [{ public_id: "e1", name: "First" }]
            : url.endsWith("judge-calendar/")
              ? { windows: [], assignments: [] }
              : url.endsWith("/stages/")
                ? [{ public_id: "s1", name: "Final" }]
                : url.endsWith("evaluation-plans/")
                  ? [{ public_id: "p1", name: "Review" }]
                  : url.endsWith("candidates/")
                    ? [
                        {
                          project: "project",
                          name: "Project",
                          status: "pending",
                        },
                      ]
                    : url.endsWith("publish-rubric/")
                      ? RUBRIC
                      : [];
        return { ok: true, status: 200, json: async () => body };
      });
    }

    it("never replays or shows one judge's queued ballots to another account", async () => {
      window.localStorage.setItem(
        `conflux.judge-outbox.judge-1.${PLAN}`,
        JSON.stringify([queued]),
      );
      // Unscoped entries from earlier versions cannot be attributed: never read or replayed.
      window.localStorage.setItem(
        `conflux.judge-outbox.${PLAN}`,
        JSON.stringify([queued]),
      );
      const fetchMock = api("judge-2");
      vi.stubGlobal("fetch", fetchMock);
      act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
      await navigateToProject();
      expect(container.textContent).not.toContain("queued");
      expect(
        fetchMock.mock.calls.some(
          ([url, init]) =>
            String(url).endsWith("/ballots/") && init?.method === "POST",
        ),
      ).toBe(false);
      // Nothing was deleted: the first judge's queue is still theirs to sync.
      expect(
        window.localStorage.getItem(`conflux.judge-outbox.judge-1.${PLAN}`),
      ).toBe(JSON.stringify([queued]));
      expect(window.localStorage.getItem(`conflux.judge-outbox.${PLAN}`)).toBe(
        JSON.stringify([queued]),
      );
    });

    it("gives the owner their own queue back", async () => {
      window.localStorage.setItem(
        `conflux.judge-outbox.judge-1.${PLAN}`,
        JSON.stringify([queued]),
      );
      const fetchMock = api("judge-1");
      // still offline for ballots so the queue is not flushed away
      const base = fetchMock.getMockImplementation()!;
      fetchMock.mockImplementation(
        async (input: unknown, init?: RequestInit) => {
          if (String(input).endsWith("/ballots/"))
            throw new TypeError("offline");
          return base(input, init);
        },
      );
      vi.stubGlobal("fetch", fetchMock);
      act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
      await navigateToProject().catch(() => undefined);
      await waitFor(
        () => container.textContent?.includes("1 ballot queued") ?? false,
      );
    });

    it("keeps the offline cache per account", async () => {
      vi.stubGlobal("fetch", api("judge-1"));
      act(() => root.render(withRouter(<JudgeWorkspace workspaceId="w" />)));
      await navigateToProject();
      expect(
        window.localStorage.getItem(`conflux.judge-cache.judge-1.${PLAN}`),
      ).not.toBeNull();
      expect(
        window.localStorage.getItem(`conflux.judge-cache..${PLAN}`),
      ).toBeNull();
      expect(
        window.localStorage.getItem(`conflux.judge-cache.${PLAN}`),
      ).toBeNull();
    });
  });
});
