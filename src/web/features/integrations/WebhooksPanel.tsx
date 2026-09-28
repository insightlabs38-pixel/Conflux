import { useEffect, useRef, useState, type FormEvent } from "react";
import { Card } from "../../components/Card";
import "./webhooks.css";

type Platform = "generic" | "discord" | "slack";
type Subscription = {
  public_id: string;
  url: string;
  event_types: string[];
  event: string | null;
  platform: Platform;
  enabled: boolean;
};
type Delivery = {
  public_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempts: number;
  last_status_code: number | null;
  last_error: string;
  next_attempt_at: string | null;
  created_at: string;
};
type Inspection = Delivery & {
  destination: string;
  next_body: string;
  body_sha256: string;
  signature_scheme: string;
  history_has_more: boolean;
  history: {
    public_id: string;
    destination: string;
    body: string;
    headers: Record<string, string>;
    started_at: string;
    completed_at: string | null;
    status_code: number | null;
    error: string;
  }[];
};

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", ...init });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail || body.url || `Webhook request failed (${response.status}).`,
    );
  }
  return response.json() as Promise<T>;
}

export function WebhooksPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/webhooks/`;
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [url, setUrl] = useState("");
  const [types, setTypes] = useState("event.status_changed");
  const [platform, setPlatform] = useState<Platform>("generic");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [destination, setDestination] = useState("");
  const selection = useRef(0);
  const inspectionRequest = useRef(0);

  async function refresh() {
    const version = selection.current;
    const items = await request<Subscription[]>(base);
    if (version !== selection.current) return;
    setSubscriptions(items);
    if (selectedId) {
      const rows = await request<Delivery[]>(
        `${base}${selectedId}/deliveries/`,
      );
      if (version !== selection.current) return;
      setDeliveries(rows);
      setHasMore(rows.length === 100);
    }
  }
  useEffect(() => {
    let active = true;
    ++selection.current;
    ++inspectionRequest.current;
    setSubscriptions([]);
    setSelectedId("");
    setInspection(null);
    setDeliveries([]);
    setSecret("");
    setError("");
    request<Subscription[]>(base)
      .then((items) => {
        if (active) setSubscriptions(items);
      })
      .catch((cause: Error) => {
        if (active) setError(cause.message);
      });
    return () => {
      active = false;
    };
  }, [base, eventId]);

  async function create(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const issued = await request<Subscription & { secret: string }>(base, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          event: eventId,
          event_types: types
            .split(",")
            .map((type) => type.trim())
            .filter(Boolean),
          platform,
        }),
      });
      setSecret(issued.secret);
      setUrl("");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function select(id: string) {
    const version = ++selection.current;
    ++inspectionRequest.current;
    setSelectedId(id);
    setInspection(null);
    setDeliveries([]);
    setHasMore(false);
    setDestination(
      subscriptions.find((item) => item.public_id === id)?.url ?? "",
    );
    setError("");
    try {
      const rows = await request<Delivery[]>(`${base}${id}/deliveries/`);
      if (version !== selection.current) return;
      setDeliveries(rows);
      setHasMore(rows.length === 100);
    } catch (cause) {
      if (version === selection.current) setError((cause as Error).message);
    }
  }

  async function inspect(id: string, older = false) {
    const version = selection.current;
    const requestId = ++inspectionRequest.current;
    const offset = older ? (inspection?.history.length ?? 0) : 0;
    setError("");
    if (!older) setInspection(null);
    try {
      const detail = await request<Inspection>(
        `${base}${selectedId}/deliveries/${id}/?offset=${offset}`,
      );
      if (
        version !== selection.current ||
        requestId !== inspectionRequest.current
      )
        return;
      setInspection((current) => ({
        ...detail,
        history: older
          ? [...(current?.history ?? []), ...detail.history]
          : detail.history,
      }));
    } catch (cause) {
      if (
        version === selection.current &&
        requestId === inspectionRequest.current
      )
        setError((cause as Error).message);
    }
  }

  async function changeDestination(event: FormEvent) {
    event.preventDefault();
    const version = selection.current;
    setError("");
    try {
      await request(`${base}${selectedId}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: destination }),
      });
      if (version !== selection.current) return;
      ++inspectionRequest.current;
      setInspection(null);
      await refresh();
    } catch (cause) {
      if (version === selection.current) setError((cause as Error).message);
    }
  }

  async function toggle(item: Subscription) {
    setError("");
    try {
      await request(`${base}${item.public_id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !item.enabled }),
      });
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function replay(deliveryId: string) {
    const version = selection.current;
    setError("");
    try {
      await request(`${base}${selectedId}/deliveries/${deliveryId}/replay/`, {
        method: "POST",
      });
      if (version === selection.current) await select(selectedId);
    } catch (cause) {
      if (version === selection.current) setError((cause as Error).message);
    }
  }

  async function loadOlder() {
    const version = selection.current;
    setError("");
    try {
      const rows = await request<Delivery[]>(
        `${base}${selectedId}/deliveries/?offset=${deliveries.length}`,
      );
      if (version !== selection.current) return;
      setDeliveries((current) => [...current, ...rows]);
      setHasMore(rows.length === 100);
    } catch (cause) {
      if (version === selection.current) setError((cause as Error).message);
    }
  }

  return (
    <Card title="Webhooks">
      <p>
        Send selected event changes to a public HTTPS endpoint. Keep the signing
        secret when it appears; it is shown once.
      </p>
      {error && <p role="alert">{error}</p>}
      {secret && (
        <p role="status">
          Signing secret: <code>{secret}</code>
        </p>
      )}
      <form onSubmit={create}>
        <label>
          Destination URL{" "}
          <input
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://example.com/webhooks"
            required
          />
        </label>
        <label>
          Event types, comma separated{" "}
          <input
            value={types}
            onChange={(event) => setTypes(event.target.value)}
            required
          />
        </label>
        <label>
          Delivery format{" "}
          <select
            value={platform}
            onChange={(event) => setPlatform(event.target.value as Platform)}
          >
            <option value="generic">Generic (signed Conflux envelope)</option>
            <option value="discord">Discord incoming webhook</option>
            <option value="slack">Slack incoming webhook</option>
          </select>
        </label>
        <button type="submit">Add webhook for this event</button>
      </form>
      <ul>
        {subscriptions
          .filter((item) => item.event === eventId || item.event === null)
          .map((item) => (
            <li key={item.public_id}>
              <strong>{item.url}</strong> ·{" "}
              {item.enabled ? "Enabled" : "Disabled"} ·{" "}
              {item.event === null ? "All events" : "This event"} ·{" "}
              {item.platform} · {item.event_types.join(", ")}
              <button type="button" onClick={() => toggle(item)}>
                {item.enabled ? "Disable" : "Enable"}
              </button>
              <button type="button" onClick={() => select(item.public_id)}>
                Delivery history
              </button>
            </li>
          ))}
      </ul>
      {selectedId && (
        <section
          aria-label="Webhook delivery history"
          className="cx-webhook-history"
        >
          <h3>Delivery history</h3>
          <form onSubmit={changeDestination}>
            <label>
              Replay destination{" "}
              <input
                type="url"
                value={destination}
                onChange={(event) => setDestination(event.target.value)}
                required
              />
            </label>
            <button type="submit">Save destination</button>
          </form>
          <p>
            Saved destinations apply to future attempts and replays. An attempt
            already sending keeps its original destination. Replays keep the
            event ID; receivers must deduplicate it.
          </p>
          <ul>
            {deliveries.map((item) => (
              <li key={item.public_id}>
                {item.event_type} · {item.status} · {item.attempts} attempts ·{" "}
                {new Date(item.created_at).toLocaleString()}
                {item.last_status_code && ` · HTTP ${item.last_status_code}`}
                {item.last_error && ` · ${item.last_error}`}
                {item.next_attempt_at &&
                  ` · Next attempt ${new Date(item.next_attempt_at).toLocaleString()}`}
                <button type="button" onClick={() => inspect(item.public_id)}>
                  Inspect
                </button>
                {item.status !== "pending" &&
                  subscriptions.find((row) => row.public_id === selectedId)
                    ?.enabled && (
                    <button
                      type="button"
                      onClick={() => replay(item.public_id)}
                    >
                      Replay
                    </button>
                  )}
              </li>
            ))}
          </ul>
          {hasMore && (
            <button type="button" onClick={loadOlder}>
              Load older deliveries
            </button>
          )}
          {inspection && (
            <section aria-label="Webhook inspection">
              <h4>Payload and signature</h4>
              <p>Next attempt destination: {inspection.destination}</p>
              <p>Next attempt body (UTF-8):</p>
              <pre>{inspection.next_body}</pre>
              <p>
                SHA-256: <code>{inspection.body_sha256}</code>
              </p>
              <p>{inspection.signature_scheme}</p>
              <p>
                Signatures below cover the exact saved body bytes and timestamp.
                Inspection sends nothing. Older deliveries may have no retained
                attempt details.
              </p>
              <ol>
                {inspection.history.map((attempt) => (
                  <li key={attempt.public_id}>
                    <p>
                      {attempt.destination} ·{" "}
                      {new Date(attempt.started_at).toLocaleString()} ·{" "}
                      {attempt.completed_at
                        ? attempt.status_code
                          ? `HTTP ${attempt.status_code}`
                          : "Failed"
                        : "Outcome unknown"}{" "}
                      {attempt.error}
                    </p>
                    <pre>{attempt.body}</pre>
                    <pre>{JSON.stringify(attempt.headers, null, 2)}</pre>
                  </li>
                ))}
              </ol>
              {inspection.history_has_more && (
                <button
                  type="button"
                  onClick={() => inspect(inspection.public_id, true)}
                >
                  Load older attempts
                </button>
              )}
            </section>
          )}
        </section>
      )}
    </Card>
  );
}
