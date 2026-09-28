import { useEffect, useState } from "react";
import { Button } from "../../components/Button";
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
  const [pending, setPending] = useState<string | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [notice, setNotice] = useState("");

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

  async function restore(entry: HistoryEntry) {
    setRestoring(true);
    setError("");
    setNotice("");
    try {
      const response = await fetch(
        `/api/v1/audit/${workspaceId}/events/${eventId}/config-history/${entry.public_id}/restore/`,
        { method: "POST", credentials: "include" },
      );
      if (!response.ok) throw new Error(`Restore failed (${response.status}).`);
      setPending(null);
      setNotice(
        "Configuration restored. Reload its editor to see the current values.",
      );
      load();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setRestoring(false);
    }
  }

  return (
    <Card title="Configuration history">
      {notice && <p role="status">{notice}</p>}
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
              {[
                "Stage",
                "TemporalGate",
                "Policy",
                "Event",
                "Track",
                "BasePrize",
              ].includes(entry.resource_type) &&
                /\.(updated|restored)$/.test(entry.action) &&
                (pending === entry.public_id ? (
                  <div>
                    <p>
                      Restore the before values shown above? Other fields keep
                      their current values.
                    </p>
                    <Button
                      disabled={restoring}
                      onClick={() => void restore(entry)}
                    >
                      Confirm restore
                    </Button>
                    <Button
                      variant="secondary"
                      disabled={restoring}
                      onClick={() => setPending(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="secondary"
                    disabled={restoring}
                    onClick={() => setPending(entry.public_id)}
                  >
                    Restore before values
                  </Button>
                ))}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
