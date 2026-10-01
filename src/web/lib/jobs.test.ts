import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "./test-http";
import {
  artifactUrl,
  followJob,
  isFinished,
  progressOf,
  type Job,
} from "./jobs";

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
  created_at: "2026-10-01T00:00:00Z",
  started_at: null,
  finished_at: null,
  artifacts: [],
  ...over,
});

function answers(...bodies: (Job | number)[]) {
  const calls: { url: string; method: string }[] = [];
  const queue = [...bodies];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url: String(url), method: init?.method ?? "GET" });
      const next = queue.length > 1 ? queue.shift()! : queue[0];
      return typeof next === "number"
        ? jsonResponse(next, { detail: "down" })
        : jsonResponse(200, next);
    }),
  );
  return calls;
}
const context = () => {
  const controller = new AbortController();
  const reports: unknown[] = [];
  return {
    controller,
    reports,
    ctx: { signal: controller.signal, report: (p: unknown) => reports.push(p) },
  };
};

afterEach(() => vi.unstubAllGlobals());

describe("jobs client", () => {
  it("describes progress honestly and knows the end states", () => {
    expect(progressOf(job())).toEqual({ label: "Waiting to start…" });
    expect(
      progressOf(
        job({
          status: "running",
          progress: { done: 1, total: 3, message: "Signing" },
        }),
      ),
    ).toEqual({ label: "Signing", done: 1, total: 3 });
    expect(progressOf(job({ status: "running" })).label).toBe("Working…");
    expect(isFinished(job({ status: "cancelling" }))).toBe(false);
    expect(isFinished(job({ status: "failed" }))).toBe(true);
    expect(artifactUrl("w", "j", "a b.json")).toBe(
      "/api/v1/workspaces/w/jobs/j/artifacts/a%20b.json/",
    );
  });

  it("follows a job to success, reporting progress on the way", async () => {
    answers(
      job({
        status: "running",
        progress: { done: 1, total: 2, message: "Half" },
      }),
      job({ status: "succeeded", result: { bytes: 5 } }),
    );
    const { ctx, reports } = context();
    const done = await followJob("w", job(), ctx, [0]);
    expect(done.status).toBe("succeeded");
    expect(reports).toEqual([
      { label: "Waiting to start…" },
      { label: "Half", done: 1, total: 2 },
      { label: "Working…" },
    ]);
  });

  it("rejects with the server's own message when the job failed or was cancelled", async () => {
    answers(
      job({
        status: "failed",
        error: { code: "invalid", message: "Pick a mode." },
      }),
    );
    await expect(followJob("w", job(), context().ctx, [0])).rejects.toThrow(
      "Pick a mode.",
    );
    answers(job({ status: "cancelled" }));
    await expect(followJob("w", job(), context().ctx, [0])).rejects.toThrow(
      "cancelled",
    );
  });

  it("tolerates a couple of failed polls but not a persistent outage or a refusal", async () => {
    answers(503, 503, job({ status: "succeeded" }));
    await expect(
      followJob("w", job(), context().ctx, [0]),
    ).resolves.toMatchObject({ status: "succeeded" });
    answers(503);
    await expect(followJob("w", job(), context().ctx, [0])).rejects.toThrow(
      "down",
    );
    const calls = answers(404);
    await expect(followJob("w", job(), context().ctx, [0])).rejects.toThrow();
    expect(calls).toHaveLength(1); // a refusal is not retried
  });

  it("asks the server to cancel when the user cancels, and stops following", async () => {
    const calls = answers(job({ status: "cancelling" }));
    const { ctx, controller } = context();
    const run = followJob("w", job(), ctx, [50]);
    controller.abort();
    await expect(run).rejects.toMatchObject({ name: "AbortError" });
    expect(calls).toEqual([
      { url: "/api/v1/workspaces/w/jobs/j1/cancel/", method: "POST" },
    ]);
  });
});
