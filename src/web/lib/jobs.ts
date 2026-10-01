import { ApiError, apiJson } from "./api";
import type { OperationContext } from "../hooks/useOperation";

/**
 * The client half of the durable job primitive (PD-F002-B01-T05). A feature's own endpoint starts
 * a job (202 and the job); this follows it to the end through `GET jobs/{id}/`, so a closed tab or
 * a slow export never loses the result: reopen the page and the job (and its download) is still
 * listed. The server owns every state; nothing here marks anything finished on its own.
 */
export type JobStatus =
  "queued" | "running" | "cancelling" | "succeeded" | "failed" | "cancelled";

export type Job = {
  public_id: string;
  kind: string;
  label: string;
  status: JobStatus;
  event: string | null;
  requested_by: string;
  progress: {
    done: number | null;
    total: number | null;
    message: string;
  } | null;
  result: Record<string, unknown> | null;
  error: { code: string; message: string } | null;
  cancellable: boolean;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  artifacts: { name: string; content_type: string; size: number }[];
};

export const jobsUrl = (workspaceId: string) =>
  `/api/v1/workspaces/${workspaceId}/jobs/`;
export const jobUrl = (workspaceId: string, jobId: string) =>
  `${jobsUrl(workspaceId)}${jobId}/`;
export const artifactUrl = (workspaceId: string, jobId: string, name: string) =>
  `${jobUrl(workspaceId, jobId)}artifacts/${encodeURIComponent(name)}/`;

export const isFinished = (job: Pick<Job, "status">) =>
  job.status === "succeeded" ||
  job.status === "failed" ||
  job.status === "cancelled";

export const getJob = (
  workspaceId: string,
  jobId: string,
  signal?: AbortSignal,
) => apiJson<Job>(jobUrl(workspaceId, jobId), "GET", undefined, signal);

export const cancelJob = (workspaceId: string, jobId: string) =>
  apiJson<Job>(`${jobUrl(workspaceId, jobId)}cancel/`, "POST");

/** Poll spacing: quick at first (most jobs are short), then gentle. */
const DELAYS = [700, 1000, 1500, 2500, 4000];
const MAX_TRANSIENT = 3;

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    if (signal.aborted) return resolve();
    const timer = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        resolve();
      },
      { once: true },
    );
  });
}

/** A short line for the user about where the job is. */
export function progressOf(job: Job) {
  const p = job.progress;
  const label =
    p?.message || (job.status === "queued" ? "Waiting to start…" : "Working…");
  return p && p.done !== null && p.total !== null
    ? { label, done: p.done, total: p.total }
    : { label };
}

/**
 * Follow a started job to its end for `useOperation`: reports progress, resolves with the finished
 * job, rejects with the server's own failure message. Aborting (the user pressed Cancel) asks the
 * server to cancel the job; it stops cooperatively, so the result of that is on the job, not here.
 * A few failed polls in a row (offline, a restart) are tolerated; the job itself keeps running.
 */
export async function followJob(
  workspaceId: string,
  start: Job,
  { signal, report }: Pick<OperationContext, "signal" | "report">,
  delays: number[] = DELAYS,
): Promise<Job> {
  let job = start;
  let step = 0;
  let transient = 0;
  for (;;) {
    if (signal.aborted) {
      await cancelJob(workspaceId, job.public_id).catch(() => undefined);
      throw new DOMException("Cancelled", "AbortError");
    }
    report(progressOf(job));
    if (isFinished(job)) break;
    await sleep(delays[Math.min(step++, delays.length - 1)], signal);
    if (signal.aborted) continue;
    try {
      job = await getJob(workspaceId, job.public_id, signal);
      transient = 0;
    } catch (error) {
      if (signal.aborted) continue;
      const retryable = !(error instanceof ApiError) || error.status >= 500;
      if (!retryable || ++transient >= MAX_TRANSIENT) throw error;
    }
  }
  if (job.status === "failed")
    throw new Error(job.error?.message ?? "The job failed.");
  if (job.status === "cancelled") throw new Error("The job was cancelled.");
  return job;
}
