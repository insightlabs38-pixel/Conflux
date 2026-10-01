// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { JobsPanel } from "./JobsPanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import type { Job } from "../../lib/jobs";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
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

const job = (over: Partial<Job> = {}): Job => ({
  public_id: "j1",
  kind: "archive_export",
  label: "Event archive export",
  status: "queued",
  event: "e1",
  requested_by: "org",
  progress: null,
  result: null,
  error: null,
  cancellable: true,
  created_at: "2026-10-01T10:00:00Z",
  started_at: null,
  finished_at: null,
  artifacts: [],
  ...over,
});
const FILE = {
  name: "e-config-archive.json",
  content_type: "application/json",
  size: 2048,
};

type Call = { url: string; method: string; body?: unknown };
async function mount(route: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call = {
        url: String(url),
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      return route(call);
    }),
  );
  await act(async () =>
    root.render(withQuery(<JobsPanel workspaceId="w" eventId="e1" />)),
  );
  await settle();
  return calls;
}
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const button = (text: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === text,
  )!;
async function until(check: () => boolean) {
  for (let i = 0; i < 200 && !check(); i++)
    await act(async () => new Promise((r) => setTimeout(r, 10)));
  expect(check()).toBe(true);
}

describe("JobsPanel", () => {
  it("starts an export, follows it to the end and offers the download", async () => {
    let polls = 0;
    const calls = await mount((call) => {
      if (call.method === "POST")
        return jsonResponse(202, job({ status: "queued" }));
      if (call.url.includes("/jobs/j1/")) {
        polls++;
        return jsonResponse(
          200,
          job({ status: "succeeded", artifacts: [FILE], cancellable: false }),
        );
      }
      return jsonResponse(200, []); // the list
    });
    expect(container.textContent).toContain("No jobs yet");

    await act(async () => button("Start export").click());
    expect(container.textContent).toMatch(
      /Starting the export|Waiting to start/,
    );
    await until(() => container.textContent!.includes("The export is ready."));
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toBe(
      "/api/v1/workspaces/w/events/e1/archive/export-jobs/",
    );
    expect(post.body).toEqual({ mode: "config", signed: false });
    expect(polls).toBeGreaterThan(0);
    const link = container.querySelector<HTMLAnchorElement>("a[download]")!;
    expect(link.getAttribute("href")).toBe(
      "/api/v1/workspaces/w/jobs/j1/artifacts/e-config-archive.json/",
    );
    expect(link.textContent).toBe("Download e-config-archive.json");
  });

  it("explains a failed job in the server's words and lets the user try again", async () => {
    await mount((call) =>
      call.method === "POST"
        ? jsonResponse(
            202,
            job({
              status: "failed",
              cancellable: false,
              error: {
                code: "invalid",
                message: "The event is not archived yet.",
              },
            }),
          )
        : jsonResponse(200, []),
    );
    await act(async () => button("Start export").click());
    await until(() => !!container.querySelector('[role="alert"]'));
    expect(container.querySelector('[role="alert"]')!.textContent).toContain(
      "The event is not archived yet.",
    );
    expect(button("Try again")).toBeDefined();
  });

  it("lists recent jobs with status, outcome and downloads, and cancels a running one", async () => {
    const list = [
      job({
        public_id: "j2",
        status: "running",
        progress: { done: 1, total: 3, message: "Signing" },
      }),
      job({
        public_id: "j3",
        status: "succeeded",
        cancellable: false,
        artifacts: [FILE],
      }),
      job({
        public_id: "j4",
        status: "failed",
        cancellable: false,
        error: {
          code: "timeout",
          message: "The job stopped reporting progress.",
        },
      }),
    ];
    const calls = await mount((call) =>
      call.method === "POST"
        ? jsonResponse(200, job({ public_id: "j2", status: "cancelling" }))
        : jsonResponse(200, list),
    );
    const rows = [...container.querySelectorAll("tbody tr")];
    expect(rows).toHaveLength(3);
    expect(rows[0].textContent).toContain("running");
    expect(rows[0].textContent).toContain("Signing");
    expect(rows[1].querySelector("a")!.textContent).toBe(FILE.name);
    expect(rows[2].textContent).toContain(
      "The job stopped reporting progress.",
    );
    expect(container.querySelectorAll("tbody button")).toHaveLength(1); // only the running one

    await act(async () =>
      container.querySelector<HTMLButtonElement>("tbody button")!.click(),
    );
    await settle();
    expect(calls.find((c) => c.method === "POST")!.url).toBe(
      "/api/v1/workspaces/w/jobs/j2/cancel/",
    );
  });

  it("shows a load failure with a retry instead of an empty list", async () => {
    let fail = true;
    await mount(() =>
      fail
        ? jsonResponse(500, { detail: "Server error" })
        : jsonResponse(200, []),
    );
    expect(container.textContent).toContain("Server error");
    fail = false;
    await act(async () => button("Try again").click());
    await settle();
    expect(container.textContent).toContain("No jobs yet");
  });
});
