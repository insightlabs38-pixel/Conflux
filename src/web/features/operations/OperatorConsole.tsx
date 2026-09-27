import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";

type EventRow = {
  public_id: string;
  name: string;
  status: string;
  is_public: boolean;
  health: "ready" | "warning" | "blocked";
  blocker_count: number;
  warning_count: number;
};
type ConsoleData = {
  event_total: number;
  events: EventRow[];
  template_total: number;
  templates: { public_id: string; name: string; source_event_name: string }[];
  activity: {
    action: string;
    actor: string | null;
    target_type: string;
    created_at: string;
  }[];
};

export function OperatorConsole({
  workspaceId,
  onChooseEvent,
}: {
  workspaceId: string;
  onChooseEvent: (id: string) => void;
}) {
  const [data, setData] = useState<ConsoleData | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    fetch(`/api/v1/workspaces/${workspaceId}/operator-console/`, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok)
          throw new Error(
            `Operator console request failed (${response.status}).`,
          );
        return response.json() as Promise<ConsoleData>;
      })
      .then((result) => {
        if (active) {
          setData(result);
          setError("");
        }
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Operator console could not load.",
          );
      });
    return () => {
      active = false;
    };
  }, [workspaceId, retry]);

  return (
    <Card title="Operator console" as="h2">
      {error && (
        <p role="alert">
          {error}{" "}
          <button type="button" onClick={() => setRetry((value) => value + 1)}>
            Retry
          </button>
        </p>
      )}
      {!data && !error && <p>Loading workspace health…</p>}
      {data && (
        <>
          <h3>Event launch readiness ({data.event_total})</h3>
          {data.events.length === 0 && <p>No events yet.</p>}
          <ul>
            {data.events.map((event) => (
              <li key={event.public_id}>
                <button
                  type="button"
                  onClick={() => onChooseEvent(event.public_id)}
                >
                  {event.name}
                </button>{" "}
                <Badge
                  tone={
                    event.health === "ready"
                      ? "success"
                      : event.health === "warning"
                        ? "warning"
                        : "danger"
                  }
                >
                  {event.health}
                </Badge>{" "}
                {event.status} · {event.is_public ? "public" : "private"} ·{" "}
                {event.blocker_count} blockers · {event.warning_count} warnings{" "}
                <a
                  href={`/api/v1/workspaces/${workspaceId}/events/${event.public_id}/archive/`}
                >
                  Archive JSON
                </a>{" "}
                <a
                  href={`/api/v1/workspaces/${workspaceId}/events/${event.public_id}/archive/signed/`}
                >
                  Signed archive
                </a>
              </li>
            ))}
          </ul>
          {data.event_total > data.events.length && (
            <p>
              Showing the most recently updated {data.events.length} events.
            </p>
          )}
          <h3>Saved templates ({data.template_total})</h3>
          {data.templates.length === 0 ? (
            <p>No saved templates.</p>
          ) : (
            <ul>
              {data.templates.map((template) => (
                <li key={template.public_id}>
                  {template.name} · source: {template.source_event_name}
                </li>
              ))}
            </ul>
          )}
          {data.template_total > data.templates.length && (
            <p>Showing the first {data.templates.length} templates.</p>
          )}
          <h3>Recent workspace activity</h3>
          {data.activity.length === 0 ? (
            <p>No operator activity yet.</p>
          ) : (
            <ul>
              {data.activity.map((item, index) => (
                <li key={`${item.created_at}-${index}`}>
                  {item.action} · {item.actor ?? "deleted user"} ·{" "}
                  {new Date(item.created_at).toLocaleString()}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </Card>
  );
}
