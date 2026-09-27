import { useEffect, useState } from "react";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";

type Signal = {
  public_id: string;
  signal_type: string;
  detail: string;
  evidence: Record<string, unknown>;
  occurred_at: string;
  resolved_at: string | null;
  resolution_note: string;
};
type AuditEntry = {
  public_id: string;
  actor: string | null;
  detail: string;
  created_at: string;
};

async function readJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", ...init });
  if (!response.ok) throw new Error(`Review request failed (${response.status}).`);
  return response.json() as Promise<T>;
}

export function FraudReview({ workspaceId, eventId }: { workspaceId: string; eventId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/voting-plan/`;
  const [signals, setSignals] = useState<Signal[]>([]);
  const [timeline, setTimeline] = useState<AuditEntry[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [moreSignals, setMoreSignals] = useState(false);
  const [moreTimeline, setMoreTimeline] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([
      readJson<Signal[]>(base + "abuse-signals/"),
      readJson<AuditEntry[]>(base + "audit/"),
    ])
      .then(([nextSignals, nextTimeline]) => {
        if (active) {
          setSignals(nextSignals);
          setTimeline(nextTimeline);
          setMoreSignals(nextSignals.length === 100);
          setMoreTimeline(nextTimeline.length === 100);
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "Review could not load.");
      });
    return () => { active = false; };
  }, [base]);

  async function resolve(signalId: string) {
    const note = notes[signalId]?.trim();
    if (!note) {
      setError("Enter a resolution note.");
      return;
    }
    setError("");
    try {
      const updated = await readJson<Signal>(base + `abuse-signals/${signalId}/resolve/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resolution_note: note }),
      });
      setSignals((current) => current.map((signal) => signal.public_id === signalId ? updated : signal));
      setTimeline(await readJson<AuditEntry[]>(base + "audit/"));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Resolution failed.");
    }
  }

  async function loadOlder(kind: "signals" | "timeline") {
    setError("");
    try {
      if (kind === "signals") {
        const older = await readJson<Signal[]>(base + `abuse-signals/?offset=${signals.length}`);
        setSignals((current) => [...current, ...older]);
        setMoreSignals(older.length === 100);
      } else {
        const older = await readJson<AuditEntry[]>(base + `audit/?offset=${timeline.length}`);
        setTimeline((current) => [...current, ...older]);
        setMoreTimeline(older.length === 100);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Older activity could not load.");
    }
  }

  return (
    <Card title="Voting review">
      {error && <p role="alert">{error}</p>}
      <h3>Abuse signals</h3>
      {signals.length === 0 ? <p>No signals recorded.</p> : (
        <ul>
          {signals.map((signal) => (
            <li key={signal.public_id}>
              <p><strong>{signal.signal_type.replaceAll("_", " ")}</strong> · {new Date(signal.occurred_at).toLocaleString()}</p>
              <p>{signal.detail}</p>
              {Object.keys(signal.evidence).length > 0 && <dl>
                {Object.entries(signal.evidence).map(([key, value]) => (
                  <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{String(value)}</dd></div>
                ))}
              </dl>}
              {signal.resolved_at ? <p>Resolved: {signal.resolution_note}</p> : (
                <div>
                  <label htmlFor={`note-${signal.public_id}`}>Resolution note</label>
                  <textarea id={`note-${signal.public_id}`} maxLength={2000}
                    value={notes[signal.public_id] ?? ""}
                    onChange={(event) => setNotes((current) => ({ ...current, [signal.public_id]: event.target.value }))} />
                  <Button onClick={() => void resolve(signal.public_id)}>Resolve signal</Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {moreSignals && <Button variant="secondary" onClick={() => void loadOlder("signals")}>Load older signals</Button>}
      <h3>Community audit</h3>
      {timeline.length === 0 ? <p>No community activity recorded.</p> : (
        <ol>
          {timeline.map((entry) => (
            <li key={entry.public_id}>
              <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time>
              {" · "}{entry.detail}{entry.actor ? ` · ${entry.actor}` : ""}
            </li>
          ))}
        </ol>
      )}
      {moreTimeline && <Button variant="secondary" onClick={() => void loadOlder("timeline")}>Load older activity</Button>}
    </Card>
  );
}
