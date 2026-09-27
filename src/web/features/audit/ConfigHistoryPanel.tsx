import { useEffect, useState } from "react";
import { Card } from "../../components/Card";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type FieldChange = { before: unknown; after: unknown };
type HistoryEntry = {
  public_id: string;
  actor: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  changes: Record<string, FieldChange>;
  created_at: string;
};

function message(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "Request failed.";
}

// Event/stage/policy/rubric configuration changes, newest first. Only rows
// with a captured before/after diff are ever returned by the API -- older
// audit rows (or ones outside this scope) never appear here, so there is
// nothing to invent on the frontend either.
export function ConfigHistoryPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    void fetch(
      `/api/v1/audit/${workspaceId}/events/${eventId}/config-history/`,
      { credentials: "include" },
    )
      .then(async (response) => {
        if (!response.ok)
          throw new Error(`Request failed (${response.status}).`);
        return (await response.json()) as HistoryEntry[];
      })
      .then(setEntries)
      .catch((cause: unknown) => setError(message(cause)));
  }
  useEffect(load, [workspaceId, eventId]);

  return (
    <Card title="Configuration history">
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && entries === null && (
        <LoadingState label="Loading configuration history…" />
      )}
      {!error && entries !== null && entries.length === 0 && (
        <p>No recorded configuration changes yet.</p>
      )}
      {!error && entries !== null && entries.length > 0 && (
        <ul className="cx-config-history">
          {entries.map((entry) => (
            <li key={entry.public_id}>
              <p>
                <strong>{entry.actor ?? "Unknown actor"}</strong> {entry.action}{" "}
                ({entry.resource_type})
                <br />
                <time dateTime={entry.created_at}>{entry.created_at}</time>
              </p>
              <dl>
                {Object.entries(entry.changes).map(([field, change]) => (
                  <div key={field}>
                    <dt>{field}</dt>
                    <dd>
                      <pre>{JSON.stringify(change.before)}</pre>
                      {" → "}
                      <pre>{JSON.stringify(change.after)}</pre>
                    </dd>
                  </div>
                ))}
              </dl>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
