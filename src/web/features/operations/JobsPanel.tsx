import { useEffect, useRef, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { DataTable } from "../../components/Foundation";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { OperationStatus } from "../../components/OperationStatus";
import { useLoad } from "../../hooks/useLoad";
import { useOperation } from "../../hooks/useOperation";
import { apiJson, describeProblem } from "../../lib/api";
import {
  artifactUrl,
  cancelJob,
  followJob,
  isFinished,
  jobsUrl,
  type Job,
  type JobStatus,
} from "../../lib/jobs";

const MODES = [
  { value: "config", label: "Configuration only" },
  { value: "full", label: "Everything the event holds" },
  { value: "final", label: "Final record (after the event)" },
];
const TONE: Record<JobStatus, "neutral" | "info" | "success" | "danger"> = {
  queued: "neutral",
  running: "info",
  cancelling: "info",
  succeeded: "success",
  failed: "danger",
  cancelled: "neutral",
};
const POLL_MS = 3000;

type Exported = { mode: string; signed: boolean };

/**
 * Background jobs of the event (PD-F002-B01-T05): start an archive export that runs on the server
 * and follow it, then find every recent job, its outcome and its download here, even after the page
 * was closed. Starting and following go through the shared job primitive (`lib/jobs.ts`).
 */
export function JobsPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [mode, setMode] = useState("config");
  const [signed, setSigned] = useState(false);
  const jobs = useLoad<Job[]>(
    `${jobsUrl(workspaceId)}?event=${eventId}&limit=15`,
    { describe: describeProblem },
  );
  const [problem, setProblem] = useState("");

  const exporting = useOperation<Exported, Job>(async (args, context) => {
    const started = await apiJson<Job>(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/archive/export-jobs/`,
      "POST",
      args,
      context.signal,
    );
    void jobs.reload();
    try {
      return await followJob(workspaceId, started, context);
    } finally {
      void jobs.reload();
    }
  });

  const rows = jobs.data ?? [];
  const active = rows.some((job) => !isFinished(job));
  const reload = useRef(jobs.reload);
  reload.current = jobs.reload;
  // While something is running the list refreshes itself; it stops once everything has finished.
  useEffect(() => {
    if (!active) return;
    const timer = setTimeout(() => void reload.current(), POLL_MS);
    return () => clearTimeout(timer);
  }, [active, rows]);

  async function cancel(job: Job) {
    setProblem("");
    try {
      await cancelJob(workspaceId, job.public_id);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Could not cancel.");
    }
    void jobs.reload();
  }

  const done =
    exporting.state.status === "success" ? exporting.state.result : null;
  return (
    <Card title="Exports and background jobs">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void exporting.start({ mode, signed });
        }}
        aria-label="Export the event archive"
      >
        <label>
          What to export{" "}
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            {MODES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          <input
            type="checkbox"
            checked={signed}
            onChange={(e) => setSigned(e.target.checked)}
          />{" "}
          Sign it so others can verify it
        </label>{" "}
        <Button type="submit" disabled={exporting.busy}>
          Start export
        </Button>
      </form>
      <OperationStatus
        state={exporting.state}
        pendingLabel="Starting the export…"
        successMessage="The export is ready."
        onCancel={exporting.cancel}
        onRetry={() => void exporting.retry()}
        onDismiss={exporting.reset}
      />
      {done?.artifacts[0] && (
        <p>
          <a
            href={artifactUrl(
              workspaceId,
              done.public_id,
              done.artifacts[0].name,
            )}
            download
          >
            Download {done.artifacts[0].name}
          </a>{" "}
          ({Math.max(1, Math.round(done.artifacts[0].size / 1024))} KB)
        </p>
      )}
      <h4>Recent jobs</h4>
      {problem && <p role="alert">{problem}</p>}
      {jobs.loading && !jobs.data && <LoadingState label="Loading jobs…" />}
      {jobs.error && (
        <ErrorState message={jobs.error.message} onRetry={jobs.reload} />
      )}
      {jobs.data && rows.length === 0 && (
        <EmptyState title="No jobs yet">
          Exports and other long operations appear here while they run and after
          they finish.
        </EmptyState>
      )}
      {rows.length > 0 && (
        <DataTable label="Recent background jobs">
          <thead>
            <tr>
              <th scope="col">Job</th>
              <th scope="col">Status</th>
              <th scope="col">Started by</th>
              <th scope="col">When</th>
              <th scope="col">Result</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((job) => (
              <tr key={job.public_id}>
                <th scope="row">{job.label}</th>
                <td>
                  <Badge tone={TONE[job.status]}>{job.status}</Badge>
                  {job.progress?.message && !isFinished(job) && (
                    <> {job.progress.message}</>
                  )}
                </td>
                <td>{job.requested_by}</td>
                <td>
                  <time dateTime={job.created_at}>
                    {new Date(job.created_at).toLocaleString()}
                  </time>
                </td>
                <td>
                  {job.error && <span role="note">{job.error.message}</span>}
                  {job.artifacts.map((a) => (
                    <a
                      key={a.name}
                      href={artifactUrl(workspaceId, job.public_id, a.name)}
                      download
                    >
                      {a.name}
                    </a>
                  ))}
                  {job.cancellable && (
                    <Button
                      variant="secondary"
                      onClick={() => void cancel(job)}
                    >
                      Cancel
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <p>
        <Button variant="secondary" onClick={() => void jobs.reload()}>
          Refresh
        </Button>
      </p>
    </Card>
  );
}
