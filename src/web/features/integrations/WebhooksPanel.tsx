import { useEffect, useState, type FormEvent } from "react";
import { Card } from "../../components/Card";

type Subscription = {
  public_id: string;
  url: string;
  event_types: string[];
  event: string | null;
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
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    setSubscriptions(await request<Subscription[]>(base));
    if (selectedId) {
      const rows = await request<Delivery[]>(
        `${base}${selectedId}/deliveries/`,
      );
      setDeliveries(rows);
      setHasMore(rows.length === 100);
    }
  }
  useEffect(() => {
    let active = true;
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
  }, [base]);

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
    setSelectedId(id);
    setError("");
    try {
      const rows = await request<Delivery[]>(`${base}${id}/deliveries/`);
      setDeliveries(rows);
      setHasMore(rows.length === 100);
    } catch (cause) {
      setError((cause as Error).message);
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
    setError("");
    try {
      await request(`${base}${selectedId}/deliveries/${deliveryId}/replay/`, {
        method: "POST",
      });
      await select(selectedId);
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function loadOlder() {
    setError("");
    try {
      const rows = await request<Delivery[]>(
        `${base}${selectedId}/deliveries/?offset=${deliveries.length}`,
      );
      setDeliveries((current) => [...current, ...rows]);
      setHasMore(rows.length === 100);
    } catch (cause) {
      setError((cause as Error).message);
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
              {item.event_types.join(", ")}
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
        <section aria-label="Webhook delivery history">
          <h3>Delivery history</h3>
          <ul>
            {deliveries.map((item) => (
              <li key={item.public_id}>
                {item.event_type} · {item.status} · {item.attempts} attempts ·{" "}
                {new Date(item.created_at).toLocaleString()}
                {item.last_status_code && ` · HTTP ${item.last_status_code}`}
                {item.last_error && ` · ${item.last_error}`}
                {item.status !== "pending" && (
                  <button type="button" onClick={() => replay(item.public_id)}>
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
        </section>
      )}
    </Card>
  );
}
