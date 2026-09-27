import { useEffect, useState } from "react";
import { Card } from "../../components/Card";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type WorkloadRow = {
  judge: string;
  assigned_count: number;
  submitted_count: number;
  completion_ratio: number;
};

function message(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "Request failed.";
}

// Organizer-only roll-up of every judge's assigned/submitted counts across
// the whole event (S24), least-complete first, so a judge falling behind
// is the first thing an organizer sees.
export function JudgeWorkloadPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [rows, setRows] = useState<WorkloadRow[] | null>(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    void fetch(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/judge-workload/`,
      { credentials: "include" },
    )
      .then(async (response) => {
        if (!response.ok)
          throw new Error(`Request failed (${response.status}).`);
        return (await response.json()) as WorkloadRow[];
      })
      .then(setRows)
      .catch((cause: unknown) => setError(message(cause)));
  }
  useEffect(load, [workspaceId, eventId]);

  return (
    <Card title="Judge workload">
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && rows === null && (
        <LoadingState label="Loading judge workload…" />
      )}
      {!error && rows !== null && rows.length === 0 && (
        <p>No judge has any assigned candidates yet.</p>
      )}
      {!error && rows !== null && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Judge</th>
              <th>Submitted</th>
              <th>Assigned</th>
              <th>Complete</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.judge}>
                <td>{row.judge}</td>
                <td>{row.submitted_count}</td>
                <td>{row.assigned_count}</td>
                <td>{Math.round(row.completion_ratio * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
